. ./vars

# create log bucket
: '
aws s3api create-bucket --bucket $logBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion 2> /dev/null
aws s3api put-bucket-acl --bucket $logBucket --grant-write URI=http://acs.amazonaws.com/groups/s3/LogDelivery --grant-read-acp URI=http://acs.amazonaws.com/groups/s3/LogDelivery
'

# create core bucket - including set bucket policy
: '
aws s3api create-bucket --bucket $coreBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion 2> /dev/null
aws s3api put-bucket-versioning --bucket $coreBucket --versioning-configuration Status=Enabled
aws s3api put-bucket-logging --bucket $coreBucket --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"'$logBucket'","TargetPrefix":"s3/'$coreBucket'/"}}'
'

# create main request bucket - including bucket policy
: '
aws s3api create-bucket --bucket $requestBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion 2> /dev/null
aws s3api put-bucket-logging --bucket $requestBucket --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"'$logBucket'","TargetPrefix":"s3/'$requestBucket'/"}}'
'

# create main server role as used by lambdas (include ...)

echo "$lambdaPolicy"

# create lambdas in main region

# create triggers between selected Lambdas and the two main buckets

# for the us-east-1 region:
    # create the edge lambda

# for each supported region:

    # create regional request bucket
    # create the regional lambdas
    # create trigger between the regional lambda and bucket
    
# create Cloudfront Distribution - including behaviours

#set core Bucket policy to allow Cloudfront access
: '
cloudfrontDistributionId='E2OGJS7FJAAP6W'
cloudfrontS3PolicyStatement='{"Effect": "Allow","Principal": {"AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity '$cloudfrontDistributionId'"},"Action": ["s3:GetObject","s3:PutObject"],"Resource": "arn:aws:s3:::'$coreBucket'/*"}'
policy='{"Statement": ['$lambdaPolicyStatement','$cloudfrontS3PolicyStatement']}'
aws s3api put-bucket-policy --bucket $coreBucket --policy $policy
'

# run core/initialise
# run core/schema

