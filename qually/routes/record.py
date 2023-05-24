from qually.helpers.route_imports import *
try:
    from flask_babel import gettext as _, force_locale
except ModuleNotFoundError:
    pass

VALID_KINDS={
    'ncmr':NCMR,
    'capa':CAPA,
    'dvtn':Deviation
}

@app.get("/<kind>-<number>")
@logged_in
def get_record_number(kind, number):

    record = get_record(kind, number)

    if request.path != record.permalink:
        return redirect(record.permalink)
    
    return render_template("record.html", record=record)

@app.post("/<kind>-<number>")
@has_seat
def post_record_number(kind, number):

    record = get_record(kind, number)

    #allow saving of future things if editable
    with force_locale(g.user.organization.lang):
        phases = [x for x in record._lifecycle if x==record._status or (x>record._status and record._lifecycle[x].get('early')=='edit')]

    entries=[]
    for phase in phases:
        entries += record._layout()[phase]

    for entry in entries:
        if entry['value'] in request.form:
            if entry['kind']=='multi':
                setattr(record, f"{entry['value']}_raw", request.form[entry['value']])
                setattr(record, entry['value'], html(request.form[entry['value']]))
                key=entry['name']
                value=txt(request.form[entry['value']])
                response=getattr(record, entry['value'])
            elif entry['kind']=='dropdown':
                setattr(record, entry['value'], int(request.form[entry['value']]))
                key=entry['name']
                value=entry['values'].get(int(request.form[entry['value']]))
                response=value
            elif entry['kind']=='user':
                n=request.form.get(entry['value'])
                if n:
                    if not g.user.organization.users.filter_by(id=int(n)).first():
                        return toast_error(_("Invalid user"))
                    setattr(record, f"{entry['value']}_id", int(n))
                    g.db.add(record)
                    g.db.flush()
                    g.db.refresh(record)
                    value=getattr(record, entry['value']).name
                else:
                    setattr(record, entry['value'], None)
                    value=""
                key=entry['name']
                response=f'<a href="{getattr(record, entry["value"]).permalink}">{getattr(record, entry["value"]).name}</a>'
            else:
                setattr(record, entry['value'], txt(request.form[entry['value']]))
                key=entry['name']
                value=getattr(record, entry['value'])
                response=value

            break
    else:
        return toast_error(_("Unable to save changes"))

    g.db.add(record)

    #clear any existing approvals on phase and log clearing

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

    return toast(_("Changes saved"), data={"new":response})

@app.post("/<kind>-<number>/status")
@has_seat
def post_record_number_status(kind, number):

    record = get_record(kind, number)

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


    #transition is approved by system, update record and log

    record._status=transition['to']
    g.db.add(record)

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

    g.db.commit()

    return toast_redirect(record.permalink)

@app.post("/<kind>-<number>/approve")
@has_seat
def post_record_number_approve(kind, number):

    record = get_record(kind, number)

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
        created_utc=g.time
        )
    g.db.add(approval)

    g.db.flush()
    
    #refresh record and get number of apprs
    #if all have approved, advance phase
    g.db.refresh(record)
    if len(record.phase_approvals(record._status)) >= len(transition['users']):
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


    g.db.commit()

    return toast_redirect(record.permalink)

@app.post("/<kind>-<number>/unapprove")
@logged_in
def post_record_number_unapprove(kind, number):

    record = get_record(kind, number)

    transition = [x for x in record._transitions[record._status] if x['id']==request.form.get('transition_id')]

    try:
        transition=transition[0]
    except IndexError:
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

    if kind not in VALID_KINDS:
        abort(404)

    OBJ=VALID_KINDS[kind]

    return render_template(f"create_record.html", obj=OBJ)

@app.get("/records/<kind>")
@logged_in
def get_record_records(kind):

    if kind not in VALID_KINDS:
        abort(404)

    listing=getattr(g.user.organization, f"{kind}s").filter(VALID_KINDS[kind]._status<100).all()

    return render_template(
        f"records.html",
        listing=listing,
        name=VALID_KINDS[kind]._name
        )


@app.post("/create_<kind>")
@has_seat
@org_update_lock
def post_record_record(kind):

    if kind not in VALID_KINDS:
        abort(404)

    OBJ = VALID_KINDS[kind]

    record=OBJ(
        owner_id=g.user.id,
        organization_id=g.user.organization.id,
        number=getattr(g.user.organization, f"next_{kind}_id"),
        created_utc=g.time
        )

    g.db.add(record)
    g.db.flush()

    with force_locale(g.user.organization.lang):
        entries=record._layout()[0]

    for entry in entries:
        if entry['value'] in request.form:
            if entry['kind']=='multi':
                setattr(record, f"{entry['value']}_raw", request.form[entry['value']])
                setattr(record, entry['value'], html(request.form[entry['value']]))
            elif entry['kind']=='dropdown':
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

    log = eval(f"{record.__class__.__name__}Log")(
        record_id=record.id,
        created_utc=g.time,
        user_id=g.user.id,
        key="State",
        value="Open"
        )
    g.db.add(log)
    g.db.commit()

    return toast_redirect(record.permalink)


@app.post("/<kind>-<number>/file")
def kind_number_add_file(kind, number):

    if kind not in VALID_KINDS:
        abort(404)

    record=get_record(kind, number)

    file=request.files.get('file')

    file_obj = File(
        organization_id=g.user.organization.id,
        creator_id=g.user.id,
        created_utc=g.time,
        ncmr_id=record.id if isinstance(record, NCMR) else None,
        capa_id=record.id if isinstance(record, CAPA) else None
        )
    g.db.add(file_obj)
    g.db.flush()
    g.db.refresh(file_obj)
    
    aws.upload_file(
        file,
        file_obj.s3_name
        )

    g.db.commit()

    return toast_redirect(record.permalink)