. ./vars

# create log bucket
aws s3api create-bucket --bucket $logBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion 2> /dev/null


# create main bucket - including set bucket policy
# aws s3api create-bucket --bucket $coreBucket --region $coreRegion 

# create main request bucket - including bucket policy

# create main server role as used by lambdas (include ...)

# create lambdas in main region

# create triggers between selected Lambdas and the two main buckets

# for the us-east-1 region:
    # create the edge lambda

# for each supported region:

    # create regional request bucket
    # create the regional lambdas
    # create trigger between the regional lambda and bucket
    
# create Cloudfront Distribution - including behaviours

# run core/initialise
# run core/schema

