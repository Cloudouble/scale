. ./vars

echo "Starting...
---------
"

echo "Checking logBucket set up for $logBucket..."
    echo "... checking if logBucket ($logBucket) exists..."
    bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
    if [[ " $bucketNames " =~ " $logBucket " ]]; then
        echo "... ... already exists."
    else
        echo "... ... NOT exists, creating now in coreRegion ($coreRegion)..."
        aws s3api create-bucket --bucket $logBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion
            bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
            if [[ " $bucketNames " =~ " $logBucket " ]]; then
                echo "... ... ... now created."
            else
                echo "... ... ... error creating logBucket ($logBucket), please try again or create this bucket manually in the  $coreRegion region. Exiting now."
                exit 1
            fi
    fi
    echo "... ensuring correct log delivery write permissions are in place..."
    ownerId=$(aws s3api get-bucket-acl --bucket $logBucket --query "Owner.ID" --output text)
    grantWrite=$(aws s3api get-bucket-acl --bucket $logBucket --query "Grants[?Permission == 'WRITE'].Grantee.URI | [0]" --output text)
    if [ "$grantWrite" == "http://acs.amazonaws.com/groups/s3/LogDelivery" ]; then
        echo "... ... write permissions in place for LogDelivery group."
    else
        echo "... ... write permissions NOT in place for LogDelivery group, enabling now..."
        aws s3api put-bucket-acl --bucket $logBucket --grant-full-control "id=$ownerId" --grant-write URI=http://acs.amazonaws.com/groups/s3/LogDelivery --grant-read-acp URI=http://acs.amazonaws.com/groups/s3/LogDelivery
        grantWrite=$(aws s3api get-bucket-acl --bucket $logBucket --query "Grants[?Permission == 'WRITE'].Grantee.URI | [0]" --output text)
        if [ "$grantWrite" == "http://acs.amazonaws.com/groups/s3/LogDelivery" ]; then
            echo "... ... ... now enabled."
        else
            echo "... ... ... error enabling write permissions for LogDelivery group, please try again or create these permissions manually for logBucket ($logBucket). Exiting now."
            exit 1
        fi
    fi
    echo "... ensuring correct log delivery read ACP permissions are in place..."
    grantReadACP=$(aws s3api get-bucket-acl --bucket $logBucket --query "Grants[?Permission == 'READ_ACP'].Grantee.URI | [0]" --output text)
    if [ "$grantReadACP" == "http://acs.amazonaws.com/groups/s3/LogDelivery" ]; then
        echo "... ... read ACP permissions in place for LogDelivery group."
    else
        echo "... ... read ACP permissions NOT in place for LogDelivery group, enabling now..."
        aws s3api put-bucket-acl --bucket $logBucket --grant-full-control "id=$ownerId" --grant-write URI=http://acs.amazonaws.com/groups/s3/LogDelivery --grant-read-acp URI=http://acs.amazonaws.com/groups/s3/LogDelivery
        grantReadACP=$(aws s3api get-bucket-acl --bucket $logBucket --query "Grants[?Permission == 'READ_ACP'].Grantee.URI | [0]" --output text)
        if [ "$grantReadACP" == "http://acs.amazonaws.com/groups/s3/LogDelivery" ]; then
            echo "... ... ... now enabled."
        else
            echo "... ... ... read ACP permissions NOT in place for LogDelivery group, please try again or create these permissions manually for logBucket ($logBucket). Exiting now."
            exit 1
        fi
    fi
    echo "... logBucket ($logBucket) correctly set up."
echo "
---------
"

echo "Checking coreBucket set up for $coreBucket..."
    echo "... checking if coreBucket ($coreBucket) exists..."
    bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
    if [[ " $bucketNames " =~ " $coreBucket " ]]; then
        echo "... ... already exists."
    else
        echo "... ... NOT exists, creating now in coreRegion ($coreRegion)..."
        aws s3api create-bucket --bucket $coreBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion
        bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
        if [[ " $bucketNames " =~ " $coreBucket " ]]; then
            echo "... ... ... now created."
        else
            echo "... ... error creating coreBucket ($coreBucket), please try again or create this bucket manually in the  $coreRegion region. Exiting now."
            exit 1
        fi
    fi
    echo "... ensuring bucket versioning is enabled..."
    coreBucketVersioning=$(aws s3api get-bucket-versioning --bucket $coreBucket --query "Status" --output text)
    if [ "$coreBucketVersioning" == "Enabled" ]; then
        echo "... ... bucket versioning enabled."
    else
        echo "... ... bucket versioning NOT enabled, enabling now..."
        aws s3api put-bucket-versioning --bucket $coreBucket --versioning-configuration Status=Enabled
        coreBucketVersioning=$(aws s3api get-bucket-versioning --bucket $coreBucket --query "Status" --output text)
        if [ "$coreBucketVersioning" == "Enabled" ]; then
            echo "... ... ... now enabled."
        else
            echo "... ... ... error enabling bucket versioning, please try again or enable this manually. Exiting now."
            exit 1
        fi
    fi
    echo "... ensuring bucket logging is correctly configured..."
    coreBucketLoggingTargetPrefix=$(aws s3api get-bucket-logging --bucket $coreBucket --query "LoggingEnabled.TargetPrefix" --output text)
    coreBucketLoggingTargetBucket=$(aws s3api get-bucket-logging --bucket $coreBucket --query "LoggingEnabled.TargetBucket" --output text)
    if [ "$coreBucketLoggingTargetPrefix" == "s3/$coreBucket/" -a "$coreBucketLoggingTargetBucket" == "$logBucket" ]; then
        echo "... ... bucket logging correctly configured."
    else
        echo "... ... bucket logging NOT correctly configured, configuring now..."
        aws s3api put-bucket-logging --bucket $coreBucket --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"'$logBucket'","TargetPrefix":"s3/'$coreBucket'/"}}'
        coreBucketLoggingTargetPrefix=$(aws s3api get-bucket-logging --bucket $coreBucket --query "LoggingEnabled.TargetPrefix" --output text)
        coreBucketLoggingTargetBucket=$(aws s3api get-bucket-logging --bucket $coreBucket --query "LoggingEnabled.TargetBucket" --output text)
        if [ "$coreBucketLoggingTargetPrefix" == "s3/$coreBucket/" -a "$coreBucketLoggingTargetBucket" == "$logBucket" ]; then
            echo "... ... ... now correctly configured."
        else
            echo "... ... ... error configuring bucket logging, please try again or enable this manually (log to $logBucket/s3/$coreBucket). Exiting now."
            exit 1
        fi
    fi
    echo "... coreBucket ($coreBucket) correctly set up."
echo "
---------
"


echo "Checking requestBucket set up for $requestBucket..."
    echo "... checking if requestBucket ($requestBucket) exists..."
    bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
    if [[ " $bucketNames " =~ " $requestBucket " ]]; then
        echo "... ... already exists."
    else
        echo "... ... NOT exists, creating now in coreRegion ($coreRegion)..."
        aws s3api create-bucket --bucket $requestBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion
        bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
        if [[ " $bucketNames " =~ " $requestBucket " ]]; then
            echo "... ... ... now created."
        else
            echo "... ... error creating requestBucket ($requestBucket), please try again or create this bucket manually in the  $coreRegion region. Exiting now."
            exit 1
        fi
    fi
    echo "... ensuring bucket logging is correctly configured..."
    requestBucketLoggingTargetPrefix=$(aws s3api get-bucket-logging --bucket $requestBucket --query "LoggingEnabled.TargetPrefix" --output text)
    requestBucketLoggingTargetBucket=$(aws s3api get-bucket-logging --bucket $requestBucket --query "LoggingEnabled.TargetBucket" --output text)
    if [ "$requestBucketLoggingTargetPrefix" == "s3/$requestBucket/" -a "$requestBucketLoggingTargetBucket" == "$logBucket" ]; then
        echo "... ... bucket logging correctly configured."
    else
        echo "... ... bucket logging NOT correctly configured, configuring now..."
        aws s3api put-bucket-logging --bucket $requestBucket --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"'$logBucket'","TargetPrefix":"s3/'$requestBucket'/"}}'
        requestBucketLoggingTargetPrefix=$(aws s3api get-bucket-logging --bucket $requestBucket --query "LoggingEnabled.TargetPrefix" --output text)
        requestBucketLoggingTargetBucket=$(aws s3api get-bucket-logging --bucket $requestBucket --query "LoggingEnabled.TargetBucket" --output text)
        if [ "$requestBucketLoggingTargetPrefix" == "s3/$requestBucket/" -a "$requestBucketLoggingTargetBucket" == "$logBucket" ]; then
            echo "... ... ... now correctly configured."
        else
            echo "... ... ... error configuring bucket logging, please try again or enable this manually (log to $logBucket/s3/$requestBucket). Exiting now."
            exit 1
        fi
    fi
    echo "... requestBucket ($requestBucket) correctly set up."
echo "
---------
"


echo "Ensuring lambdaPolicy ($lambdaPolicyName) is created correctly..."
    lambdaPolicy="${lambdaPolicy#"${lambdaPolicy%%[![:space:]]*}"}"
    lambdaPolicy="${lambdaPolicy%"${lambdaPolicy##*[![:space:]]}"}" 
    lambdaPolicyVersion=$(aws iam get-policy --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --query "Policy.DefaultVersionId" --output text)
    if [ ! "$lambdaPolicyVersion" ]; then
        echo "... ... NOT exists, creating now..."
        aws iam create-policy --policy-name $lambdaPolicyName --policy-document "$lambdaPolicy" --region $coreRegion
        lambdaPolicyVersion=$(aws iam get-policy --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --query "Policy.DefaultVersionId" --output text)
        if [ "$lambdaPolicyVersion" ]; then
            echo "... ... ... lambdaPolicy ($lambdaPolicyName) created."
        else 
            echo "... ... ... error creating lambdaPolicy ($lambdaPolicyName), please try again or create this manually:"
            echo ""
            echo "Policy Name: $lambdaPolicyName"
            echo "Policy Document: "
            echo "$lambdaPolicy"
            echo ""
            echo "... ... ... Exiting now."
            exit 1
        fi
    else
        echo "... already exists, checking policy document..."
        lambdaPolicyDocument=$(aws iam get-policy-version --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --version-id "$lambdaPolicyVersion" --query "PolicyVersion.Document" --output json)
        if [ "$lambdaPolicyDocument" != "$lambdaPolicy" ]; then
            echo "... ... policy document is not correct, correcting now..."
            deleteVersion=$(aws iam list-policy-versions --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --query "Versions[?!IsDefaultVersion].VersionId | [0]" --output text)
            aws iam delete-policy-version --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --version-id "$deleteVersion"
            aws iam create-policy-version --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --policy-document "$lambdaPolicy" --set-as-default --region $coreRegion
            lambdaPolicyDocument=$(aws iam get-policy-version --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName" --version-id "$lambdaPolicyVersion" --query "PolicyVersion.Document" --output json)
            if [ "$lambdaPolicyDocument" == "$lambdaPolicy" ]; then
                echo "... ... ... now corrected."
            else 
                echo "... ... ... error correcting lambdaPolicy ($lambdaPolicyName), please try again or correct this manually:"
                echo ""
                echo "Policy Name: $lambdaPolicyName"
                echo "Policy Document: "
                echo "$lambdaPolicy"
                echo ""
                echo "... ... ... Exiting now."
                exit 1
            fi
        fi
    fi
    echo "... lambdaPolicy policy is correct."
echo "
---------
"


echo "Ensuring lambdaRole ($lambdaRole) exists and if correctly configured..."
    assumeRolePolicy="${assumeRolePolicy#"${assumeRolePolicy%%[![:space:]]*}"}"
    assumeRolePolicy="${assumeRolePolicy%"${assumeRolePolicy##*[![:space:]]}"}" 
    lambdaRoleListGetName=$(aws iam list-roles --query "Roles[?RoleName == '$lambdaRole'].RoleName | [0]" --output text)
    echo "... checking exists..."
    if [ "$lambdaRoleListGetName" != "$lambdaRole" ]; then 
        echo "... ... NOT exists, creating now..."
        aws iam create-role --role-name "$lambdaRole" --assume-role-policy-document "$assumeRolePolicy" --region $coreRegion
        lambdaRoleListGetName=$(aws iam list-roles --query "Roles[?RoleName == '$lambdaRole'].RoleName | [0]" --output text)
        if [ "$lambdaRoleListGetName" == "$lambdaRole" ]; then 
            echo "... ... ... now created."
        else 
            echo "... ... ... error creating role $lambdaRole, please try again or create this manually. Exiting now."
            exit 1
        fi
    fi
    echo "... checking that the Assume Role Policy is correct..."
    lambdaRoleAssumeRolePolicyDocument=$(aws iam list-roles --query "Roles[?RoleName == '$lambdaRole'].AssumeRolePolicyDocument | [0]" --output json)
    if [ "$lambdaRoleAssumeRolePolicyDocument" == "$assumeRolePolicy" ]; then
        echo "... ... assumeRolePolicy is correct."
    else
        echo "... ... assumeRolePolicy is NOT correct, correcting now..."
        aws iam update-assume-role-policy --role-name "$lambdaRole" --policy-document "$assumeRolePolicy" --region $coreRegion
        lambdaRoleAssumeRolePolicyDocument=$(aws iam list-roles --query "Roles[?RoleName == '$lambdaRole'].AssumeRolePolicyDocument | [0]" --output json)
        if [ "$lambdaRoleAssumeRolePolicyDocument" == "$assumeRolePolicy" ]; then
            echo "... ... now corrected."
        else
            echo "... ... ... error correcting the Assume Role Policy for role $lambdaRole, please try again or correct this manually:"
            echo ""
            echo "Role Name: $lambdaRole"
            echo "Assume Role Policy Document: "
            echo "$assumeRolePolicy"
            echo ""
            echo "... ... ... Exiting now."
            exit 1
        fi
    fi
    echo "... check that the $lambdaPolicyName is attached to $lambdaRole..."
    attachPolicyArn="arn:aws:iam::$accountId:policy/$lambdaPolicyName"
    attachedRolePoliciesArn=$(aws iam list-attached-role-policies --role-name $lambdaRole --query "AttachedPolicies[?PolicyName == '$lambdaPolicyName'].PolicyArn" --output text)
    if [ "$attachPolicyArn" == "$attachedRolePoliciesArn" ]; then
        echo "... ... is already attached."
    else 
        echo "... ... is NOT attached, attaching now..."
        aws iam attach-role-policy --role-name "$lambdaRole" --policy-arn "arn:aws:iam::$accountId:policy/$lambdaPolicyName"  --region $coreRegion
        attachedRolePoliciesArn=$(aws iam list-attached-role-policies --role-name $lambdaRole --query "AttachedPolicies[?PolicyName == '$lambdaPolicyName'].PolicyArn" --output text)
        if [ "$attachPolicyArn" == "$attachedRolePoliciesArn" ]; then
            echo "... ... ... now attached."        
        else
            echo "... ... ... error attaching policy ($lambdaPolicyName) to role ($lambdaRole), please try again or do this manually. Exiting now."
            exit 1
        fi
    fi
    echo "... lambdaRole exists and is properly configured."    
echo "
---------
"


echo "Ensuring core Lambda functions are available in $coreRegion..."
cd core
for functionName in *; do
    lambdaName="$lambdaNamespace-core-$functionName"
    echo "... checking if $lambdaName exists..."
    existingFunctionArn="$(aws lambda list-functions --region $coreRegion --query "Functions[?FunctionName == '$lambdaName'].FunctionArn | [0]" --output text)"
    if [ "$existingFunctionArn" ]; then
        echo "... ... $lambdaName already exists."
    else
        echo "... ... $lambdaName NOT exists, creating now..."
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
        aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish --region $coreRegion
        unlink temp/main.py
        rmdir temp
        unlink $functionName.zip
        if [ 'request' = $functionName ]; then
            echo "... ... creating trigger from requestBucket ($requestBucket) to request lambda ($lambdaName)..."
            notificationConfiguration='{"LambdaFunctionConfigurations": [{"Id": "request", "LambdaFunctionArn": "arn:aws:lambda:'$coreRegion':'$accountId':function:'$lambdaName'","Events": ["s3:ObjectCreated:*"]}]}'
            aws s3api put-bucket-notification-configuration --bucket $requestBucket --notification-configuration "$notificationConfiguration"
            echo "... ... ... trigger created."
        fi
        cd ../
        existingFunctionArn="$(aws lambda list-functions --region $coreRegion --query "Functions[?FunctionName == '$lambdaName'].FunctionArn | [0]" --output text)"
        if [ "$existingFunctionArn" ]; then
            echo "... ... ... $lambdaName created."
        else
            echo "... ... ... error creating $lambdaName, please try again or create it manually in $coreRegion: "
            echo "Function Name: $lambdaName"
            echo "Runtime: Python3.8"
            echo "Handler: main.main"
            echo "Role: $lambdaRoleArn"
            echo "Timeout: 900"
            echo "Code: use $functionName/main.py"
            echo "... ... ... exiting now..."
            exit 1
        fi
    fi
done
cd ..
echo "
---------
"


echo "Ensuring trigger Lambda functions are available in $coreRegion..."
cd trigger
for functionName in *; do
    lambdaName="$lambdaNamespace-trigger-$functionName"
    echo "... checking if $lambdaName exists..."
    existingFunctionArn="$(aws lambda list-functions --region $coreRegion --query "Functions[?FunctionName == '$lambdaName'].FunctionArn | [0]" --output text)"
    if [ "$existingFunctionArn" ]; then
        echo "... ... $lambdaName already exists."
    else
        echo "... ... $lambdaName NOT exists, creating now..."
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
        aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish --region $coreRegion
        unlink temp/main.py
        rmdir temp
        unlink $functionName.zip
        if [ 'proxy' = $functionName ]; then
            echo "... ... creating trigger from coreBucket ($coreBucket) to trigger proxy lambda ($lambdaName)..."
            notificationConfiguration='{"LambdaFunctionConfigurations": [{"LambdaFunctionArn": "arn:aws:lambda:'$coreRegion':'$accountId:'function:'$lambdaName'","Events": ["s3:ObjectCreated:*","s3:ObjectRemoved:*"]}]}'
            aws s3api put-bucket-notification-configuration --bucket $coreBucket --notification-configuration "$notificationConfiguration"
        fi
        cd ../
        existingFunctionArn="$(aws lambda list-functions --region $coreRegion --query "Functions[?FunctionName == '$lambdaName'].FunctionArn | [0]" --output text)"
        if [ "$existingFunctionArn" ]; then
            echo "... ... ... $lambdaName created."
        else
            echo "... ... ... error creating $lambdaName, please try again or create it manually in $coreRegion: "
            echo "Function Name: $lambdaName"
            echo "Runtime: Python3.8"
            echo "Handler: main.main"
            echo "Role: $lambdaRoleArn"
            echo "Timeout: 900"
            echo "Code: use $functionName/main.py"
            echo "... ... ... exiting now..."
            exit 1
        fi
    fi
done
cd ..
echo "
---------
"


exit 0 






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


