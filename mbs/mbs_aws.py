import boto3

from mbs.mbs_log import init_logger

mbs_common_logger = init_logger()


def upload_bill_to_s3_and_get_object_path(user_id):
    user_id = str(user_id)
    s3 = boto3.resource('s3')
    bucket_name = 'mbsdemo'
    data = open(user_id + '.pdf', 'rb')
    s3.Bucket('mbsdemo').put_object(Key='bills/' + user_id + '.pdf', Body=data, ACL='public-read')
    location = boto3.client('s3').get_bucket_location(Bucket=bucket_name)['LocationConstraint']
    url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket_name, 'bills/' + user_id + '.pdf')
    mbs_common_logger.critical('Successfully uploaded the bill to ' + url)
    return url
