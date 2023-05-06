import boto3

from os import remove
from io import BytesIO
from qually.__main__ import app

#set up AWS connection
S3 = boto3.client(
	"s3",
	aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],
	aws_secret_access_key=app.config["AWS_SECRET_ACCESS_KEY"]
	)

def crop_and_resize(img, resize):

    i = img

    # get constraining dimension
    org_ratio = i.width / i.height
    new_ratio = resize[0] / resize[1]

    if new_ratio > org_ratio:
        crop_height = int(i.width / new_ratio)
        box = (0, (i.height // 2) - (crop_height // 2),
               i.width, (i.height // 2) + (crop_height // 2))
    else:
        crop_width = int(new_ratio * i.height)
        box = ((i.width // 2) - (crop_width // 2), 0,
               (i.width // 2) + (crop_width // 2), i.height)

    return i.resize(resize, box=box)

def upload_file(name, file resize=None):

	tempname=name.replace("/","_")

	file.save(tempname)

	if resize:
        i = Image.open(tempname)
        i = crop_and_resize(i, resize)
        i.save(tempname)

	S3.upload_file(
		tempname,
		Bucket=app.config["S3_BUCKET"],
		Key=name,
		ExtraArgs={
			"ContentType":"image/png",
			"StorageClass":"INTELLIGENT_TIERING"
			}
		)

	remove(tempname)

def download_file(name):

	b=BytesIO()

	S3.download_fileobj(
		app.config["S3_BUCKET"],
		name,
		b
		)
	b.seek(0)
	return b

def delete_file(name):

	S3.delete_object(
	    Bucket=app.config["S3_BUCKET"],
	    Key=name
	)