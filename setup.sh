. ./vars

echo "Starting...
...
"

echo "Retrieving list of existing buckets..."
bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
echo "Retrieved list of existing buckets."
echo "
...
"

echo "Checking if logBucket ($logBucket) exists..."
if [[ " $bucketNames " =~ " $logBucket " ]]; then
    echo "... already exists."
else
    echo "... NOT exists, creating now in coreRegion ($coreRegion)..."
    aws s3api create-bucket --bucket $logBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion
    echo "... now created."
fi
echo "Ensuring correct log delivery permissions are in place..."
aws s3api put-bucket-acl --bucket $logBucket --grant-write URI=http://acs.amazonaws.com/groups/s3/LogDelivery --grant-read-acp URI=http://acs.amazonaws.com/groups/s3/LogDelivery
echo "Correct log delivery permissions are in place."
echo "
...
"

echo "Checking if coreBucket ($coreBucket) exists..."
if [[ " $bucketNames " =~ " $coreBucket " ]]; then
    echo "... already exists."
else
    echo "... NOT exists, creating now in coreRegion ($coreRegion)..."
    aws s3api create-bucket --bucket $coreBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion
    aws s3api put-bucket-versioning --bucket $coreBucket --versioning-configuration Status=Enabled
    aws s3api put-bucket-logging --bucket $coreBucket --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"'$logBucket'","TargetPrefix":"s3/'$coreBucket'/"}}'
    echo "... now created."
fi
echo "
...
"

echo "Checking if requestBucket ($requestBucket) exists..."
if [[ " $bucketNames " =~ " $requestBucket " ]]; then
    echo "... already exists."
else
    echo "... NOT exists, creating now in coreRegion ($coreRegion)..."
    aws s3api create-bucket --bucket $requestBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion
    aws s3api put-bucket-logging --bucket $requestBucket --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"'$logBucket'","TargetPrefix":"s3/'$requestBucket'/"}}'
    echo "... now created."
fi
echo "
...
"

echo "Ensuring lambdaPolicy ($lambdaPolicyName) is correct..."
lambdaPolicy="${lambdaPolicy#"${lambdaPolicy%%[![:space:]]*}"}"
lambdaPolicy="${lambdaPolicy%"${lambdaPolicy##*[![:space:]]}"}" 
lambdaPolicyVersion=$(aws iam get-policy --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --query "Policy.DefaultVersionId" --output text)
if [ ! "$lambdaPolicyVersion" ]; then
    echo "... NOT exists, creating now..."
    aws iam create-policy --policy-name $lambdaPolicyName --policy-document "$lambdaPolicy" --region $coreRegion
    echo "... lambdaPolicy ($lambdaPolicyName) created."
else
    echo "... already exists, checking policy document..."
    lambdaPolicyDocument=$(aws iam get-policy-version --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --version-id "$lambdaPolicyVersion" --query "PolicyVersion.Document" --output json)
    if [ "$lambdaPolicyDocument" != "$lambdaPolicy" ]; then
        echo "... ... policy document is not correct, correcting now..."
        deleteVersion=$(aws iam list-policy-versions --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --query "Versions[?!IsDefaultVersion].VersionId | [0]" --output text)
        aws iam delete-policy-version --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --version-id "$deleteVersion"
        aws iam create-policy-version --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --policy-document "$lambdaPolicy" --set-as-default --region $coreRegion
        echo "... ... now corrected."
    fi
fi
echo "lambdaPolicy policy is correct."
echo "
...
"

echo "Ensuring lambdaRole ($lambdaRole) exists..."
lambdaRoleAssumeRolePolicyDocument=$(aws iam list-roles --query "Roles[?RoleName == '$lambdaRole'].AssumeRolePolicyDocument | [0]" --output json)
if [ "${#lambdaRoleAssumeRolePolicyDocument}" -le 10 ]; then 
    echo "... NOT exists, creating now..."
    aws iam create-role --role-name "$lambdaRole" --assume-role-policy-document "$assumeRolePolicy" --region $coreRegion
    echo "... now created."
    echo "... attaching policy ($lambdaPolicyName) to role."
    aws iam attach-role-policy --role-name "$lambdaRole" --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName"  --region $coreRegion
    echo "... now attached."
else
    echo "... already exists, checking assumeRolePolicy..."
    if [ "$lambdaRoleAssumeRolePolicyDocument" != "$assumeRolePolicy" ]; then
        echo "... ... assumeRolePolicy is NOT correct, correcting now..."
        aws iam update-assume-role-policy --role-name "$lambdaRole" --policy-document "$assumeRolePolicy" --region $coreRegion
        echo "... ... now corrected."
    fi
    echo "... checking if lambdaPolicy ($lambdaPolicyName) is attached..."
    attachedPolicyArn=$(aws iam list-attached-role-policies --role-name "$lambdaRole" --region $coreRegion --query "AttachedPolicies[?PolicyName == '$lambdaPolicyName'].PolicyArn" --output text)
    if [ ! "$attachedPolicyArn" ]; then
        echo "... ... lambdaPolicy is NOT attached, attaching now..."
        aws iam attach-role-policy --role-name "$lambdaRole" --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName"  --region $coreRegion
        echo "... ... now attached."
    else
        echo "... ... lambdaPolicy is already attached."
    fi
fi
echo "
...
"

# create core lambdas in core region
echo "Creating core Lambda functions in $coreRegion..."
cd core
for functionName in *; do
    lambdaName="$lambdaNamespace-core-$functionName"
    echo "... creating $lambdaName..."
    $existingFunctionArn=$(aws lambda get-function --function-name "$lambdaName" --region "$coreRegion" --query "Configuration.FunctionArn" --output text 2>/dev/null) 2>/dev/null
    if [ "$existingFunctionArn" ]; then
        echo "... ... already exists."
        continue
    fi

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
    echo "$lambdaName"
    #aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish true --region $coreRegion
    unlink temp/main.py
    rmdir temp
    unlink $functionName.zip
    if [ 'request' = $functionName ]; then
        echo "... ... creating trigger from requestBucket ($requestBucket) and request lambda ($lambdaName)..."
        # create trigger between the core request lambda and core request bucket
        #aws s3api put-bucket-notification-configuration --bucket $requestBucket --notification-configuration '{"LambdaFunctionConfigurations": [{"LambdaFunctionArn": "arn:aws:lambda:'$coreRegion':'$accountId:'function:'$lambdaName'","Events": ["s3:ObjectCreated:*"]}]}'
        echo "... ... ... trigger created."
    fi
    cd ../
    echo "... $lambdaName created."
done
cd ..




exit 0 




# create trigger lambdas in core region
<< COMMENT
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
COMMENT

# create extension lambdas in core region
<< COMMENT
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
COMMENT


# for the edge region NOT COMPLETE YET:
<< COMMENT
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
COMMENT


# for each supported region:
<< COMMENT
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
COMMENT


# create Cloudfront Distribution - including behaviours
<< COMMENT
dCoreOrigin='{"Id": "'$coreBucket'", "DomainName": "'$coreBucket'.s3.amazonaws.com", "OriginPath": "", "OriginShield": false, "ConnectionAttempts": 3, "ConnectionTimeout": 10}'
dErrorOrigin='{"Id": "'$coreBucket'-403", "DomainName": "'$coreBucket'.s3.amazonaws.com", "OriginPath": "/'$envSystemRoot'/error/403.html", "OriginShield": false, "ConnectionAttempts": 3, "ConnectionTimeout": 10}'
dOrigins='{"Quantity": 2, "Items": ['$dCoreOrigin', '$dErrorOrigin']}'
dCachePolicyIdStandard=$(aws cloudfront list-cache-policies --type custom --query 'CachePolicyList.Items[?CachePolicy.CachePolicyConfig.Name == "'$systemProperName'Standard"].CachePolicy.Id')
if [ ! $dCachePolicyIdStandard ]; then
    dCachePolicyIdStandard=$(aws cloudfront create-cache-policy --query "Id" --cache-policy-config '{"Name": "'$systemProperName'Standard", '\
        '"ParametersInCacheKeyAndForwardedToOrigin": {"EnableAcceptEncodingGzip": true, "EnableAcceptEncodingBrotli": true, '\
        '"HeadersConfig": {"Quantity": 3, "Items": ["Accept", "Access-Control-Request-Method", "Access-Control-Request-Headers"]}}}')
fi
dCachePolicyIdDisabled=$(aws cloudfront list-cache-policies --type custom --query 'CachePolicyList.Items[?CachePolicy.CachePolicyConfig.Name == "'$systemProperName'Disabled"].CachePolicy.Id')
if [ ! $dCachePolicyIdDisabled ]; then
    dCachePolicyIdDisabled=$(aws cloudfront create-cache-policy --query "Id" --cache-policy-config '{"Name": "'$systemProperName'Disabled", '\
        '"ParametersInCacheKeyAndForwardedToOrigin": {"EnableAcceptEncodingGzip": true, "EnableAcceptEncodingBrotli": true, "DefaultTTL": 0, "MinTTL": 0, "MaxTTL": 0 '\
        '"HeadersConfig": {"Quantity": 3, "Items": ["Accept", "Access-Control-Request-Method", "Access-Control-Request-Headers"]}}}')
fi
dOriginRequestPolicyIdStandard=$(aws cloudfront list-origin-request-policies --type custom --query "OriginRequestPolicyList.Items[?OriginRequestPolicy.OriginRequestPolicyConfig.Name == "'$systemProperName'Standard"].OriginRequestPolicy.Id")
if [ ! $dOriginRequestPolicyIdStandard ]; then
    dOriginRequestPolicyIdStandard=$(aws cloudfront create-origin-request-policy --query "Id" --cache-policy-config '{"Name": "'$systemProperName'Standard", '\
        '"HeadersConfig": {"HeaderBehavior": "whitelist", "Headers": {"Quantity": 3, "Items: ["Accept", "Access-Control-Request-Method", "Access-Control-Request-Headers"]}}, '\
        '"CookiesConfig": {"CookieBehavior": "none"}, "QueryStringsConfig": {"QueryStringBehavior": "none"}}')
fi
dLambdaFunctionAssociations='{"Quantity": 1, "Items": [{"LambdaFunctionARN": "arn:aws:lambda:'$edgeRegion':'$accountId':function:'$lambdaNamespace'-edge-accept", "EventType": "origin-request", "IncludeBody": true}]}'
dDefaultCacheBehaviour='{"TargetOriginId": "'$coreBucket'", "ViewerProtocolPolicy": "redirect-to-https", "AllowedMethods": {"Quantity": 3, "Items": ["GET", "HEAD", "OPTIONS"], '\
    '"CachedMethods": {"Quantity": 3, "Items": ["GET", "HEAD", "OPTIONS"]}}, "Compress": true, '\
    '"LambdaFunctionAssociations": '$dLambdaFunctionAssociations', "CachePolicyId": "'$dCachePolicyIdStandard'", "OriginRequestPolicyId": "'$dOriginRequestPolicyIdStandard'"}'
dWriteCacheBehavior='{"TargetOriginId": "'$coreBucket'", "ViewerProtocolPolicy": "redirect-to-https", "AllowedMethods": {"Quantity": 3, "Items": ["GET", "HEAD", "OPTIONS"], '\
    '"CachedMethods": {"Quantity": 3, "Items": ["GET", "HEAD", "OPTIONS"]}}, "Compress": true, '\
    '"LambdaFunctionAssociations": '$dLambdaFunctionAssociations', "CachePolicyId": "'$dCachePolicyIdStandard'", "OriginRequestPolicyId": "'$dOriginRequestPolicyIdStandard'"}'
dCacheBehaviorItemsArray=()
for PathPattern in ${!cacheBehaviors[@]}; do 
    dCacheBehaviorItemsArray+='{"PathPattern": "'$PathPattern'", "TargetOriginId": "'${cacheBehaviors[$PathPattern]['TargetOriginId']}'", "ViewerProtocolPolicy": "redirect-to-https", "AllowedMethods": '${cacheBehaviors[$PathPattern]['AllowedMethods']}', '\
    '"CachedMethods": {"Quantity": 3, "Items": ["GET", "HEAD", "OPTIONS"]}, "Compress": true, '\
    '"LambdaFunctionAssociations": '${cacheBehaviors[$PathPattern]['LambdaFunctionAssociations']}', "CachePolicyId": "'${cacheBehaviors[$PathPattern]['CachePolicyId']}'", "OriginRequestPolicyId": "'${cacheBehaviors[$PathPattern]['OriginRequestPolicyId']}'"}, '
done
dCacheBehaviorItems="[${dCacheBehaviorItemsArray::-2}]"
dCacheBehaviors='{"Quantity": 15, "Items": '$dCacheBehaviorItems'}'

dCustomErrorResponses='{"Quantity": 1, "Items": [{"ErrorCode": 403, "ResponsePagePath": "/'$envSystemRoot'/error/403.html", "ResponseCode": 403, "ErrorCachingMinTTL": 10}]}'
dLogging='{"Enabled": true, "IncludeCookies": true, "Bucket": "'$logBucket'", "Prefix": "cloudfront/'$systemProperName'/"}'

distributionConfig='{"CallerReference": "'$systemProperName'", "DefaultRootObject": "index.html", "Origins": '\
    $dOrigins', "DefaultCacheBehavior": '$dDefaultCacheBehaviour', "CacheBehaviors": '$dCacheBehaviors', "CustomErrorResponses": '$dCustomErrorResponses' "Comment": "'\
    $systemProperName'" "Logging": '$dLogging', "PriceClass": "PriceClass_All", "Enabled": true, "ViewerCertificate": {"CloudFrontDefaultCertificate": true}, "IsIPV6Enabled": true}'

cloudfrontDistributionId=$(aws cloudfront create-distribution --query "Distribution.Id" --distribution-config $distributionConfig)
'

#set core Bucket policy to allow Cloudfront access
: '
cloudfrontS3PolicyStatement='{"Effect": "Allow","Principal": {"AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity '$cloudfrontDistributionId'"},"Action": ["s3:GetObject","s3:PutObject"],"Resource": "arn:aws:s3:::'$coreBucket'/*"}'
aws s3api put-bucket-policy --bucket $coreBucket --policy '{"Statement": ['$lambdaPolicyStatement','$cloudfrontS3PolicyStatement']}'


# run core/schema
    aws lambda invoke --function-name "$lambdaNamespace-core-schema" --invocation-type "RequestResponse" --log-type "Tail" --payload '{}'

# run core/initialise
    sudoKey=uuidgen
    initialisePayload='{"key": "'$sudoKey'", "name": "'$sudoName'", "_env": {"bucket": "'$coreBucket'", "lambda_namespace": "'$lambdaNamespace'", "data_root": "'$envSystemRoot'"}}'
    aws lambda invoke --function-name "$lambdaNamespace-core-initialise" --invocation-type "RequestResponse" --log-type "Tail" --payload $initialisePayload
    
COMMENT
    
#print sudoKey to console
echo "Your sudo key is: " 
echo ""
echo "$sudoKey"
echo ""
echo "Copy it now as it will not be displayed again"


