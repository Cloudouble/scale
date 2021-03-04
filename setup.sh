. ./vars

# create log bucket
: '
aws s3api create-bucket --bucket $logBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion # 2> /dev/null
aws s3api put-bucket-acl --bucket $logBucket --grant-write URI=http://acs.amazonaws.com/groups/s3/LogDelivery --grant-read-acp URI=http://acs.amazonaws.com/groups/s3/LogDelivery
'

# create core bucket - including set bucket policy
: '
aws s3api create-bucket --bucket $coreBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion
aws s3api put-bucket-versioning --bucket $coreBucket --versioning-configuration Status=Enabled
aws s3api put-bucket-logging --bucket $coreBucket --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"'$logBucket'","TargetPrefix":"s3/'$coreBucket'/"}}'
'

# create main request bucket - including bucket policy
: '
aws s3api create-bucket --bucket $requestBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion 2> /dev/null
aws s3api put-bucket-logging --bucket $requestBucket --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"'$logBucket'","TargetPrefix":"s3/'$requestBucket'/"}}'
'

# create main server role as used by lambdas (include ...)
: '
aws iam create-policy --policy-name $lambdaPolicyName --policy-document "$lambdaPolicy" --region $coreRegion
aws iam create-role --role-name $lambdaRoleName --assume-role-policy-document "$assumeRolePolicy" --region $coreRegion
'

# create core lambdas in core region
: '
cd core
for functionName in *; do
    lambdaName="$lambdaNamespace-core-$functionName"
    echo $lambdaName
    cd "$functionName/"
    if [ ! -d 'temp' ]; then
        mkdir temp
    fi
    cp main.py ./temp
    cd temp
    if [ 'request' = $functionName ]; then
        sed -i "1s/.*/$lambdaEnvCoreRequest/" main.py
    fi
    if [ 'schema' = $functionName ]; then
        sed -i "1s/.*/$lambdaEnvCoreSchema/" main.py
    fi
    zip ../$functionName.zip main.py
    cd ../
    #aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish true --region $coreRegion
    unlink temp/main.py
    rmdir temp
    unlink $functionName.zip
    if [ 'request' = $functionName ]; then
        # create trigger between the core request lambda and core request bucket
        aws s3api put-bucket-notification-configuration --bucket $requestBucket --notification-configuration '{"LambdaFunctionConfigurations": [{"LambdaFunctionArn": "arn:aws:lambda:'$coreRegion':'$accountId:'function:'$lambdaName'","Events": ["s3:ObjectCreated:*"]}]}'
    fi
    cd ../
done
cd ..
'

# create trigger lambdas in core region
: '
cd trigger
for functionName in *; do
    lambdaName="$lambdaNamespace-trigger-$functionName"
    echo $lambdaName
    cd "$functionName/"
    if [ ! -d 'temp' ]; then
        mkdir temp
    fi
    cp main.py ./temp
    cd temp
    if [ 'proxy' = $functionName ]; then
        sed -i "1s/.*/$lambdaEnvTriggerProxy/" main.py
    fi
    zip ../$functionName.zip main.py
    cd ../
    #aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish true --region $coreRegion
    unlink temp/main.py
    rmdir temp
    unlink $functionName.zip
    if [ 'proxy' = $functionName ]; then
        # create trigger between the trigger proxy lambda and core bucket
        '{"LambdaFunctionConfigurations": [{"LambdaFunctionArn": "arn:aws:lambda:'$coreRegion':'$accountId:'function:'$lambdaName'","Events": ["s3:ObjectCreated:*","s3:ObjectRemoved:*"]}]}'
        aws s3api put-bucket-notification-configuration --bucket $coreBucket --notification-configuration 
    fi
    cd ../
done
cd ..
'

# create extension lambdas in core region
: '
cd extension
for scope in *; do
    cd $scope
    for functionName in *; do
        if [ '*' = $functionName ]; then
            break
        fi
        lambdaName="$lambdaNamespace-extension-$scope-$functionName"
        echo $lambdaName
        cd "$functionName/"
        if [ ! -d 'temp' ]; then
            mkdir temp
        fi
        cp main.py ./temp
        cd temp
        zip ../$functionName.zip main.py
        cd ../
        #aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish true --region $coreRegion
        unlink temp/main.py
        rmdir temp
        unlink $functionName.zip
        cd ../
    done
    cd ../
done
cd ..
'


# for the edge region NOT COMPLETE YET:
: '
cd edge
bucketsArray=()
for key in ${!requestBuckets[@]}; do 
    bucketsArray+="'$key': '${requestBuckets[$key]}', "
done
bucketsString="buckets = {${bucketsArray::-2}}"
for functionName in *; do
    lambdaName="$lambdaNamespace-edge-$functionName"
    echo $lambdaName
    cd "$functionName/"
    if [ ! -d 'temp' ]; then
        mkdir temp
    fi
    cp main.py ./temp
    cd temp
    sed -i "1s/.*/$bucketsString/" main.py
    zip ../$functionName.zip main.py
    cd ../
    #aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish true --region $edgeRegion
    unlink temp/main.py
    rmdir temp
    unlink $functionName.zip
    cd ../
done
cd ..
'


# for each supported region:
: '
cd region
for key in ${!requestBuckets[@]}; do 
    if [ '_' = $key ]; then
        useRegion=$coreRegion
    fi
    if [ '_' != $key ]; then
        useRegion=$key
    fi
    # create regional request bucket
    aws s3api create-bucket --bucket ${requestBuckets[$key]} --region $useRegion --create-bucket-configuration LocationConstraint=$useRegion
    aws s3api put-bucket-logging --bucket ${requestBuckets[$key]} --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"'$logBucket'","TargetPrefix":"s3/'${requestBuckets[$key]}'/"}}'
    # create the regional lambdas
    for functionName in *; do
        lambdaName="$lambdaNamespace-region-$functionName"
        echo $lambdaName
        cd "$functionName/"
        if [ ! -d 'temp' ]; then
            mkdir temp
        fi
        cp main.py ./temp
        cd temp
        sed -i "1s/.*/$lambdaEnvRegion/" main.py
        zip ../$functionName.zip main.py
        cd ../
        #aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish true --region $useRegion
        unlink temp/main.py
        rmdir temp
        unlink $functionName.zip
        if [ 'request' = $functionName ]; then
            # create trigger between the regional lambda and bucket
            aws s3api put-bucket-notification-configuration --bucket ${requestBuckets[$key]} --notification-configuration '{"LambdaFunctionConfigurations": [{"LambdaFunctionArn": "arn:aws:lambda:'$useRegion':'$accountId:'function:'$lambdaName'","Events": ["s3:ObjectCreated:*"]}]}'
        fi
        cd ../
    done
done
cd ../
'


# create Cloudfront Distribution - including behaviours

dCoreOrigin='{"Id": "'$coreBucket'", "DomainName": "'$coreBucket'.s3.amazonaws.com", "OriginPath": "", "OriginShield": false, "ConnectionAttempts": 3, "ConnectionTimeout": 10}'
dErrorOrigin='{"Id": "'$coreBucket'", "DomainName": "'$coreBucket'.s3.amazonaws.com", "OriginPath": "/'$envSystemRoot'/error/403.html", "OriginShield": false, "ConnectionAttempts": 3, "ConnectionTimeout": 10}'
dOrigins='{"Quantity": 2, "Items": ['$dCoreOrigin', '$dErrorOrigin']}'

dDefaultCacheBehaviour='{}'
dCacheBehaviors='[]'
dCustomErrorResponses='{}'
dLogging='{}'

distributionConfig='{"CallerReference": "'$systemProperName'", "DefaultRootObject": "index.html", "Origins": '\
    $dOrigins', "DefaultCacheBehavior": '$dDefaultCacheBehaviour', "CacheBehaviors": '$dCacheBehaviors', "CustomErrorResponses": '$dCustomErrorResponses' "Comment": "'\
    $systemProperName'" "Logging": '$dLogging', "PriceClass": "PriceClass_All", "Enabled": true, "ViewerCertificate": {"CloudFrontDefaultCertificate": true}, "IsIPV6Enabled": true}'


#cloudfrontDistributionId=$(aws cloudfront create-distribution --query "Distribution.Id")
#echo $cloudfrontDistributionId

#set core Bucket policy to allow Cloudfront access
: '
cloudfrontDistributionId='E2OGJS7FJAAP6W'
cloudfrontS3PolicyStatement='{"Effect": "Allow","Principal": {"AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity '$cloudfrontDistributionId'"},"Action": ["s3:GetObject","s3:PutObject"],"Resource": "arn:aws:s3:::'$coreBucket'/*"}'
aws s3api put-bucket-policy --bucket $coreBucket --policy '{"Statement": ['$lambdaPolicyStatement','$cloudfrontS3PolicyStatement']}'
'

# run core/initialise
# run core/schema

