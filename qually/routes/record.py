from qually.helpers.route_imports import *
try:
    from flask_babel import gettext as _, force_locale
except ModuleNotFoundError:
    pass


@app.get("/<kind>-<number>")
@app.get("/<kind>-<number>/revision/<rev>")
@logged_in
def get_record_number(kind, number, rev=None):

    record = g.user.organization.get_record(kind, number, rev=rev)

    if rev and request.path != record.display_revision.permalink:
        return redirect(record.display_revision.permalink)
    elif not rev and request.path != record.permalink:
        return redirect(record.permalink)

    #on view hook
    record._on_view()

    return render_template("record.html", record=record)

@app.post("/<kind>-<number>")
@has_seat
def post_record_number(kind, number):

    record = g.user.organization.get_record(kind, number)

    key, value, response, do_reload = record._edit_form()

    if not key:
        return toast_error(_("Unable to save changes"))

    #clear any existing approvals on phase and log clearing
    if getattr(record, "approvals", None):
        approvals_cleared = g.db.query(eval(f"{record.__class__.__name__}Approval")).filter_by(record_id=record.id, status_id=record._status).delete()
        if approvals_cleared:

            with force_locale(g.user.organization.lang):
                appr_clear_log=eval(f"{record.__class__.__name__}Log")(
                    user_id=g.user.id,
                    record_id=record.id,
                    created_utc=g.time,
                    key=f"{_('Approvals')} - {record.status}",
                    value=_("Cleared"),
                    created_ip=request.remote_addr
                    )
                g.db.add(appr_clear_log)
    else:
        approvals_cleared=False

    if getattr(record, "logs", None):
        with force_locale(g.user.organization.lang):
            log=eval(f"{record.__class__.__name__}Log")(
                user_id=g.user.id,
                record_id=record.id,
                created_utc=g.time,
                key=key,
                value=value,
                created_ip=request.remote_addr
                )
            g.db.add(log)

    g.db.commit()

    if do_reload or approvals_cleared:
        return toast_redirect(record.permalink)

    return toast(_("Changes saved"), data={"new":response})

@app.post("/<kind>-<number>/status")
@has_seat
def post_record_number_status(kind, number):

    record = g.user.organization.get_record(kind, number)

    transition = [x for x in record._transitions[record._status] if x['id']==request.form.get('transition_id')]

    try:
        transition=transition[0]
    except IndexError:
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    if g.user not in transition['users']:
        return toast_error(_("You are not authorized to do that."), 403)

    if transition.get("approval"):
        return toast_error(_("This transition requires approval signatures."), 403)

    if transition['to']<100 and (not record._lifecycle[transition['to']]['users'] or not record._lifecycle[transition['to']]['users'][0]):
        return toast_error(_("A user must be assigned to the {x} phase first.").format(x=record._lifecycle[transition['to']]['name']), 409)

    #check for required
    if transition['to']!=101 and transition['to']>record._status:
        for entry in record._layout()[record._status]:
            if entry.get('required') and not getattr(record, entry['value']):
                return toast_error(_("Missing value for required field {x}").format(x=entry['name']), 400)


    #transition is approved by system, update record and log

    record._status=transition['to']
    g.db.add(record)

    if getattr(record, "logs", None):
        with force_locale(g.user.organization.lang):
            log=eval(f"{record.__class__.__name__}Log")(
                user_id=g.user.id,
                record_id=record.id,
                created_utc=g.time,
                key=_("Status"),
                value=record.status,
                created_ip=request.remote_addr
                )

        g.db.add(log)

    #delete any pre-existing approvals on the new status
    if getattr(record, "approvals", None):
        for approval in record.approvals:
            if approval.status_id==record._status:
                g.db.delete(approval)

    #Phase change hook
    record._after_phase_change()

    g.db.commit()

    return toast_redirect(record.permalink)

@app.post("/<kind>-<number>/approve")
@has_seat
def post_record_number_approve(kind, number):

    record = g.user.organization.get_record(kind, number)

    transition = [x for x in record._transitions[record._status] if x['id']==request.form.get('transition_id')]

    try:
        transition=transition[0]
    except IndexError:
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    if g.user not in transition['users']:
        return toast_error(_("You are not authorized to do that."), 403)

    if record.has_approved:
        return toast_error(_("You already approved this."))

    if transition['to']<100 and (not record._lifecycle[transition['to']]['users'] or not record._lifecycle[transition['to']]['users'][0]):
        return toast_error(_("A user must be assigned to the {x} phase first.").format(x=record._lifecycle[transition['to']]['name']), 409)

    ## Validate password
    if not check_password_hash(g.user.passhash, request.form.get("password")):
        return toast_error(_("Incorrect password"), 403)

    if not transition.get("approval"):
        return toast_error(_("This transition does not require approval signatures."), 403)

    #check for required
    if transition['to']!=101:
        for entry in record._layout()[record._status]:
            if entry.get('required') and not getattr(record, entry['value']):
                return toast_error(_("Missing value for required field {x}").format(x=entry['name']), 400)

    #approval is approved by system, update data log

    with force_locale(g.user.organization.lang):
        appr_log=eval(f"{record.__class__.__name__}Log")(
            user_id=g.user.id,
            record_id=record.id,
            created_utc=g.time,
            key=f"{_('Approvals')} - {record.status}",
            value=_("Approved"),
            created_ip=request.remote_addr
            )
        g.db.add(appr_log)

    approval=eval(f"{record.__class__.__name__}Approval")(
        user_id=g.user.id,
        record_id=record.id,
        status_id=record._status,
        created_utc=g.time,
        user_name = g.user.name
        )
    g.db.add(approval)

    g.db.commit()
    
    #refresh record and get number of apprs
    #if all have approved, advance phase
    g.db.refresh(record)
    phase_approvals=record.phase_approvals(record._status)

    #if there are custom logic relationships, run that,
    #otherwise, all must approve
    if transition.get("approval_logic"):

        phase_approvers=[x.user for x in phase_approvals]
        for rel in transition.get("approval_logic"):
            if rel.group.requires_all and not all([x in phase_approvers for x in [y.user for y in rel.group.user_relationships]]):
                return toast_redirect(record.permalink)
            elif not any([x in phase_approvers for x in [y.user for y in rel.group.user_relationships]]):
                return toast_redirect(record.permalink)


    elif len(phase_approvals) < len(transition['users']):
        return toast_redirect(record.permalink)


    record._status=transition['to']
    g.db.add(record)
    log=eval(f"{record.__class__.__name__}Log")(
        user_id=g.user.id,
        record_id=record.id,
        created_utc=g.time,
        key=_("Status"),
        value=record.status,
        created_ip=request.remote_addr
        )

    g.db.add(log)

    #delete any pre-existing approvals on the new status
    for approval in record.approvals:
        if approval.status_id==record._status:
            g.db.delete(approval)

    #phase change hook
    record._after_phase_change()


    g.db.commit()

    return toast_redirect(record.permalink)

@app.post("/<kind>-<number>/unapprove")
@logged_in
def post_record_number_unapprove(kind, number):

    record = g.user.organization.get_record(kind, number)

    if int(request.form.get("status"))!=record._status:
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    approvals = [x for x in record.approvals if x.user_id==g.user.id and x.status_id==record._status]

    if not approvals:
        return toast_error(_("You don't have any approvals to clear."))

    for approval in approvals:
        g.db.delete(approval)
    g.db.flush()

    with force_locale(g.user.organization.lang):
        appr_log=eval(f"{record.__class__.__name__}Log")(
            user_id=g.user.id,
            record_id=record.id,
            created_utc=g.time,
            key=f"{_('Approvals')} - {record.status}",
            value=_("Unapproved"),
            created_ip=request.remote_addr
            )
        g.db.add(appr_log)

    g.db.commit()

    return toast_redirect(record.permalink)

    
@app.get("/create_<kind>")
@has_seat
def get_create_record(kind):

    if kind not in ALL_PROCESSES:
        abort(404)

    OBJ=ALL_PROCESSES[kind]

    return render_template(f"create_record.html", obj=OBJ)

@app.get("/records/<kind>")
@logged_in
def get_record_records(kind):

    if kind not in ALL_PROCESSES:
        abort(404)


    if hasattr(ALL_PROCESSES[kind], "_view_class"):

        views=g.db.query(
                    ALL_PROCESSES[kind]._view_class
                    ).filter_by(user_id=g.user.id).subquery()

        listing=getattr(g.user.organization, f"{kind}s").join(
            views,
            ALL_PROCESSES[kind].id==views.c.record_id
            ).order_by(views.c.created_utc.desc()).limit(20).all()


    else:
        listing=getattr(g.user.organization, f"{kind}s").filter(ALL_PROCESSES[kind]._status<100).all()

    return render_template(
        f"records.html",
        listing=listing,
        obj=ALL_PROCESSES[kind],
        name=ALL_PROCESSES[kind].name_readable()
        )


@app.post("/create_<kind>")
@has_seat
@org_update_lock
def post_record_record(kind):

    if kind not in ALL_PROCESSES:
        abort(404)

    OBJ = ALL_PROCESSES[kind]

    record=OBJ(
        owner_id=g.user.id,
        organization_id=g.user.organization.id,
        created_utc=g.time,
        number=OBJ._next_number(),
        )

    g.db.add(record)
    g.db.flush()

    with force_locale(g.user.organization.lang):
        entries=record._layout()[0]

    for entry in entries:
        # if entry.get("required") and request.form.get(entry['value']) in ['',None]:
        #     return toast_error(_("Provide response for {x}").format(x=entry['name']))
        if entry['value'] in request.form:
            if entry['kind']=='multi':
                setattr(record, f"{entry['value']}_raw", request.form[entry['value']])
                setattr(record, entry['value'], html(request.form[entry['value']]))
            elif entry['kind']=='dropdown':
                if int(request.form[entry['value']]) not in entry['values']:
                    return toast_error(_("Invalid selection for {x}").format(x=entry['name']))
                setattr(record, entry['value'], int(request.form[entry['value']]))
            elif entry['kind']=='user':
                n=request.form.get(entry['value'])
                if n:
                    setattr(record, f"{entry['value']}_id", int(request.form[entry['value']]))
                else:
                    setattr(record, f"{entry['value']}_id", None)
            else:
                setattr(record, entry['value'], txt(request.form[entry['value']]))

    g.db.add(record)
    g.db.flush()

    record._after_create()

    with force_locale(g.user.organization.lang):
        log = eval(f"{record.__class__.__name__}Log")(
            record_id=record.id,
            created_utc=g.time,
            user_id=g.user.id,
            key=_("State"),
            value=record._lifecycle[0]['name'],
            created_ip=request.remote_addr
            )
        g.db.add(log)
    g.db.commit()

    return toast_redirect(record.permalink)


@app.post("/<kind>-<number>/file")
def kind_number_add_file(kind, number):

    record=g.user.organization.get_record(kind, number)

    if not record.can_edit(int(request.form.get("status_id"))):
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    source=record._lifecycle[int(request.form.get("status_id"))].get("object_data", record)

    uploads=request.files.getlist('file')
    for upload in uploads:

        file_obj = File(
            organization_id=g.user.organization.id,
            creator_id=g.user.id,
            created_utc=g.time,
            status_id=int(request.form.get("status_id")),
            ncmr_id=source.id if isinstance(source, NCMR) else None,
            capa_id=source.id if isinstance(source, CAPA) else None,
            dvtn_id=source.id if isinstance(source, Deviation) else None,
            rvsn_id=source.id if isinstance(source, ItemRevision) else source.effective_revision.id if isinstance(source, Item) else None,
            chng_id = source.id if isinstance(source, ChangeOrder) else None,
            file_name=upload.filename
            )

        g.db.add(file_obj)
        g.db.flush()
        g.db.refresh(file_obj)
        
        aws.upload_file(
            file_obj.s3_name,
            upload
            )

        g.db.flush()

    with force_locale(g.user.organization.lang):
        log = eval(f"{record.__class__.__name__}Log")(
            record_id=record.id,
            created_utc=g.time,
            user_id=g.user.id,
            key=_("Files"),
            value=_("Upload to {stage}: {names}").format(
                stage=record._lifecycle[int(request.form.get("status_id"))]['name'], 
                names=", ".join([x.filename for x in uploads])
                ),
            created_ip=request.remote_addr
            )
        g.db.add(log)

    g.db.commit()

    return toast_redirect(record.permalink)

@app.post("/<kind>-<number>/file/<fid>/delete")
def kind_number_delete_file(kind, number, fid):

    record=g.user.organization.get_record(kind, number)

    file_obj=[f for f in record.files if f.id==int(fid, 36)][0]

    status=file_obj.status_id

    if not record.can_edit(status):
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    name=file_obj.file_name

    aws.delete_file(file_obj.s3_name)

    g.db.delete(file_obj)

    g.db.flush()

    with force_locale(g.user.organization.lang):
        log = eval(f"{record.__class__.__name__}Log")(
            record_id=record.id,
            created_utc=g.time,
            user_id=g.user.id,
            key=_("Files"),
            value=_("Delete from {stage}: {name}").format(
                stage=record._lifecycle[status]['name'], 
                name=name),
            created_ip=request.remote_addr
            )
        g.db.add(log)

    g.db.commit()
    return toast_redirect(record.permalink)
