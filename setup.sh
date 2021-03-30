. ./vars


echo "
---------
---------

LiveElement Scale installation starting...
---------
"

echo "Checking logBucket set up for $logBucket..."
    echo "... checking if logBucket ($logBucket) exists..."
    bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
    if [[ " $bucketNames " =~ " $logBucket " ]]; then
        echo "... ... already exists."
        aws s3api put-public-access-block --bucket $logBucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    else
        echo "... ... NOT exists, creating now in coreRegion ($coreRegion)..."
        if [ "us-east-1" = "$coreRegion" ]; then
            aws s3api create-bucket --bucket $logBucket --region $coreRegion 
        else
            aws s3api create-bucket --bucket $logBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion
        fi
        aws s3api put-public-access-block --bucket $logBucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
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
        aws s3api put-public-access-block --bucket $coreBucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    else
        echo "... ... NOT exists, creating now in coreRegion ($coreRegion)..."
        if [ "us-east-1" = "$coreRegion" ]; then
            aws s3api create-bucket --bucket $coreBucket --region $coreRegion 
        else
            aws s3api create-bucket --bucket $coreBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion
        fi
        aws s3api put-public-access-block --bucket $coreBucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
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
    echo "... ensuring bucket CORS permissions is correctly configured..."
    coreBucketCorsCurrent=$(aws s3api get-bucket-cors --bucket $coreBucket --output json)
    if [ "$coreBucketCors" == "$coreBucketCorsCurrent" ]; then
        echo "... ... bucket CORS permissions correctly configured."
    else
        echo "... ... bucket CORS permission NOT correctly configured, configuring now..."
        coreBucketCors=$(aws s3api put-bucket-cors --bucket $coreBucket --cors-configuration "$coreBucketCors")
        echo "... ... ... now correctly configured."
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
        aws s3api put-public-access-block --bucket $requestBucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    else
        echo "... ... NOT exists, creating now in coreRegion ($coreRegion)..."
        if [ "us-east-1" = "$coreRegion" ]; then
            aws s3api create-bucket --bucket $requestBucket --region $coreRegion 
        else
            aws s3api create-bucket --bucket $requestBucket --region $coreRegion --create-bucket-configuration LocationConstraint=$coreRegion
        fi
        aws s3api put-public-access-block --bucket $requestBucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
        bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
        if [[ " $bucketNames " =~ " $requestBucket " ]]; then
            echo "... ... ... now created."
        else
            echo "... ... error creating requestBucket ($requestBucket), please try again or create this bucket manually in the  $coreRegion region. Exiting now."
            exit 1
        fi
    fi
    echo "...ensuring bucket lifecycle configuration is correct..."
    requestBucketLifeCycleConfigurationCurrent=$(aws s3api get-bucket-lifecycle-configuration --bucket $requestBucket --output json)
    if [ "$requestBucketLifeCycleConfiguration" == "$requestBucketLifeCycleConfigurationCurrent" ]; then
        echo "... ... lifecycle configuration is correct"
    else
        echo "... ... lifecycle configuration is NOT correct, configuring now..."
        requestBucketLifeCycleConfigurationCurrent=$(aws s3api put-bucket-lifecycle-configuration --bucket $requestBucket --lifecycle-configuration "$requestBucketLifeCycleConfiguration" --expected-bucket-owner "$accountId" --output json)
        echo "... ... ... now correctly configured"
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


echo "Ensuring lambdaRole ($lambdaRole) exists and is correctly configured..."
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
            echo "Role Name: $lambdaRole"
            echo "Role Use Case: Lambda"
            echo "(optional) Role Policy to attach: $lambdaPolicyName"
            echo "(optional) Assume Role Policy Document: "
            echo "$assumeRolePolicy"
            exit 1
        fi
    fi
    echo "... checking that the Assume Role Policy is correct..."
    lambdaRoleAssumeRolePolicyDocument=$(aws iam list-roles --query "Roles[?RoleName == '$lambdaRole'].AssumeRolePolicyDocument | [0]" --output json)
    lambdaRoleAssumeRolePolicyDocument="${lambdaRoleAssumeRolePolicyDocument#"${lambdaRoleAssumeRolePolicyDocument%%[![:space:]]*}"}"
    lambdaRoleAssumeRolePolicyDocument="${lambdaRoleAssumeRolePolicyDocument%"${lambdaRoleAssumeRolePolicyDocument##*[![:space:]]}"}" 
    if [ "$lambdaRoleAssumeRolePolicyDocument" == "$assumeRolePolicy" ]; then
        echo "... ... assumeRolePolicy is correct."
    else
        echo "... ... assumeRolePolicy is NOT correct, correcting now..."
        aws iam update-assume-role-policy --role-name "$lambdaRole" --policy-document "$assumeRolePolicy" --region $coreRegion
        echo "... ... ... now corrected."
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
    if [ ${#existingFunctionArn} -ge 10 ]; then
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
        if [ 'socket' = $functionName ]; then
            sed -i "1s/.*/$lambdaEnvCoreRequest/" main.py
        fi
        zip ../$functionName.zip main.py
        cd ../
        aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish --region $coreRegion
        unlink temp/main.py
        rmdir temp
        unlink $functionName.zip
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
            echo "Code: use core/$functionName/main.py"
            echo "... ... ... exiting now..."
            exit 1
        fi
        cd ../
    fi
    if [ 'request' = $functionName ]; then
        echo "... ... checking if trigger from requestBucket ($requestBucket) to request lambda ($lambdaName) exists..."
        getNotificationConfigurations=$(aws s3api get-bucket-notification-configuration --bucket $requestBucket --query "LambdaFunctionConfigurations[?Id == '$functionName'].Id | [0]" --output text)
        if [ ! "$getNotificationConfigurations" == "$functionName" ]; then
            echo "... ... ... NOT exists, creating now..."
            notificationConfiguration='{"LambdaFunctionConfigurations": [{"Id": "'$functionName'","LambdaFunctionArn": "arn:aws:lambda:'$coreRegion':'$accountId':function:'$lambdaName'","Events":["s3:ObjectCreated:*"]}]}'
            aws lambda add-permission --region $coreRegion --function-name "arn:aws:lambda:$coreRegion:$accountId:function:$lambdaName" --action "lambda:InvokeFunction" --statement-id "request" --principal "s3.amazonaws.com" --source-account "$accountId" --source-arn "arn:aws:s3:::$requestBucket"
            aws s3api put-bucket-notification-configuration --bucket $requestBucket --notification-configuration "$notificationConfiguration"
            getNotificationConfigurations=$(aws s3api get-bucket-notification-configuration --bucket $requestBucket --query "LambdaFunctionConfigurations[?Id == '$functionName'].Id | [0]" --output text)
            if [ "$functionName" == "$getNotificationConfigurations" ]; then
                echo "... ... ... ... trigger created."
            else 
                echo "... ... ... ... error creating trigger, please try again or create it manually: "
                echo "Lambda Function: $lambdaName"
                echo "Trigger Name: $functionName"
                echo "Trigger Type: S3"
                echo "Trigger Event: Any Object Created"
                echo "Bucket: $requestBucket"
                echo "... ... ... ... exiting now."
                exit 1
            fi
        else
            echo "... ... ... already exists."
        fi
    fi
done
cd ../
echo "
---------
"


echo "Ensuring trigger Lambda functions are available in $coreRegion..."
cd trigger
for functionName in *; do
    lambdaName="$lambdaNamespace-trigger-$functionName"
    echo "... checking if $lambdaName exists..."
    existingFunctionArn="$(aws lambda list-functions --region $coreRegion --query "Functions[?FunctionName == '$lambdaName'].FunctionArn | [0]" --output text)"
    if [ ${#existingFunctionArn} -ge 10 ]; then
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
            echo "Code: use trigger/$functionName/main.py"
            echo "... ... ... exiting now..."
            exit 1
        fi
        cd ../
    fi
    if [ 'proxy' = $functionName ]; then
        echo "... ... checking if trigger from coreBucket ($coreBucket) to proxy lambda ($lambdaName) exists..."
        getNotificationConfigurations=$(aws s3api get-bucket-notification-configuration --bucket $coreBucket --query "LambdaFunctionConfigurations[?Id == '$functionName'].Id | [0]" --output text)
        if [ ! "$getNotificationConfigurations" == "$functionName" ]; then
            echo "... ... ... NOT exists, creating now..."
            notificationConfiguration='{"LambdaFunctionConfigurations": [{"Id": "'$functionName'", "LambdaFunctionArn": "arn:aws:lambda:'$coreRegion':'$accountId:'function:'$lambdaName'","Events":["s3:ObjectCreated:*","s3:ObjectRemoved:*"]}]}'
            aws lambda add-permission --region $coreRegion --function-name "arn:aws:lambda:$coreRegion:$accountId:function:$lambdaName" --action "lambda:InvokeFunction" --statement-id "request" --principal "s3.amazonaws.com" --source-account "$accountId" --source-arn "arn:aws:s3:::$coreBucket"
            aws s3api put-bucket-notification-configuration --bucket $coreBucket --notification-configuration "$notificationConfiguration"
            getNotificationConfigurations=$(aws s3api get-bucket-notification-configuration --bucket $coreBucket --query "LambdaFunctionConfigurations[?Id == '$functionName'].Id | [0]" --output text)
            if [ "$functionName" == "$getNotificationConfigurations" ]; then
                echo "... ... ... ... trigger created."
            else 
                echo "... ... ... ... error creating trigger, please try again or create it manually: "
                echo "Lambda Function: $lambdaName"
                echo "Trigger Name: $functionName"
                echo "Trigger Type: S3"
                echo "Trigger Event: Any Object created, Any Object removed"
                echo "Bucket: $coreBucket"
                echo "... ... ... ... exiting now."
                exit 1
            fi
        else
            echo "... ... ... already exists."
        fi
    fi
done
cd ../
echo "
---------
"


echo "Ensuring extension Lambda functions are available in $coreRegion..."
cd extension
for scope in *; do
    cd $scope
    for functionName in *; do
        if [ '*' = $functionName ]; then
            break
        fi
        lambdaName="$lambdaNamespace-extension-$scope-$functionName"
        echo "... checking if $lambdaName exists..."
        existingFunctionArn="$(aws lambda list-functions --region $coreRegion --query "Functions[?FunctionName == '$lambdaName'].FunctionArn | [0]" --output text)"
        if [ ${#existingFunctionArn} -ge 10 ]; then
            echo "... ... $lambdaName already exists."
        else
            echo "... ... $lambdaName NOT exists, creating now..."
            cd "$functionName/"
            if [ ! -d 'temp' ]; then
                mkdir temp
            fi
            cp main.py ./temp
            cd temp
            zip ../$functionName.zip main.py
            cd ../
            aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish --region $coreRegion
            unlink temp/main.py
            rmdir temp
            unlink $functionName.zip
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
                echo "Code: use extension/$scope/$functionName/main.py"
                echo "... ... ... exiting now..."
                exit 1
            fi
        fi
    done
    cd ../
done
cd ../
echo "
---------
"


echo "Ensuring edge Lambda functions are available in $edgeRegion..."
cd edge
bucketsArray=()
for key in ${!requestBuckets[@]}; do 
    bucketsArray+="'$key': '${requestBuckets[$key]}', "
done
bucketsString="buckets = {${bucketsArray::-2}}"
for functionName in *; do
    lambdaName="$lambdaNamespace-edge-$functionName"
    echo "... checking if $lambdaName exists..."
    existingFunctionArn="$(aws lambda list-functions --region $edgeRegion --query "Functions[?FunctionName == '$lambdaName'].FunctionArn | [0]" --output text)"
    if [ "${#existingFunctionArn}" -ge 10 ]; then
        echo "... ... $lambdaName already exists."
    else
        echo "... ... $lambdaName NOT exists, creating now..."
        cd "$functionName/"
        if [ ! -d 'temp' ]; then
            mkdir temp
        fi
        cp main.py ./temp
        cd temp
        sed -i "1s/.*/$bucketsString/" main.py
        zip ../$functionName.zip main.py
        cd ../
        aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 30 --publish --region $edgeRegion
        unlink temp/main.py
        rmdir temp
        unlink $functionName.zip
        cd ../
        existingFunctionArn="$(aws lambda list-functions --region $edgeRegion --query "Functions[?FunctionName == '$lambdaName'].FunctionArn | [0]" --output text)"
        if [ "$existingFunctionArn" ]; then
            echo "... ... ... $lambdaName created."
        else
            echo "... ... ... error creating $lambdaName, please try again or create it manually in $edgeRegion: "
            echo "Function Name: $lambdaName"
            echo "Runtime: Python3.8"
            echo "Handler: main.main"
            echo "Role: $lambdaRoleArn"
            echo "Timeout: 30"
            echo "Code: use edge/$functionName/main.py"
            echo "... ... ... exiting now..."
            exit 1
        fi
    fi
    if [ "accept" == "$functionName" ]; then
        echo "... ... getting version number of latest version of accept function..."
        acceptFunctionVersion=$(aws lambda list-versions-by-function --region $edgeRegion --function-name "$lambdaName" --query "Versions[?Version != '\$LATEST'].Version | [0]" --output text)
        if [ ! "$acceptFunctionVersion" ]; then
            echo "... ... ... no version created, creating one now..."
            acceptFunctionVersion=$(aws lambda publish-version --region $edgeRegion --function-name "$lambdaName" --query "Version" --output text)
            if [ "$acceptFunctionVersion" ]; then
                echo "... ... ... ... version $acceptFunctionVersion created."                
            else
                echo "... ... ... ... error creating version for $lambdaName, please try again or create it manually. Exiting now."
                exit 1
            fi
        else
            echo "... ... ... version $acceptFunctionVersion already exists."
        fi
    fi
done
cd ../
echo "
---------
"


echo "Ensuring region Lambda functions and request buckets are available in each supported region..."
cd region
for key in ${!requestBuckets[@]}; do 
    if [ '_' = $key ]; then
        useRegion=$coreRegion
    fi
    if [ '_' != $key ]; then
        useRegion=$key
    fi
    echo "... checking region $useRegion..."
        echo "... ... checking if bucket ${requestBuckets[$key]} exists..."
        bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
        if [[ " $bucketNames " =~ " ${requestBuckets[$key]} " ]]; then
            echo "... ... ... already exists."
            aws s3api put-public-access-block --bucket ${requestBuckets[$key]} --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
        else
            echo "... ... ... NOT exists, creating now in $useRegion..."
            if [ "us-east-1" = "$useRegion" ]; then
                aws s3api create-bucket --bucket ${requestBuckets[$key]} --region $useRegion 
            else
                aws s3api create-bucket --bucket ${requestBuckets[$key]} --region $useRegion --create-bucket-configuration LocationConstraint=$useRegion
            fi
            aws s3api put-public-access-block --bucket ${requestBuckets[$key]} --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
            bucketNames=' '$(aws s3api list-buckets --query "join(' ', Buckets[].Name)")' '
            if [[ " $bucketNames " =~ " ${requestBuckets[$key]} " ]]; then
                echo "... ... ... now created."
            else
                echo "... ... ... error creating bucket ${requestBuckets[$key]} in $useRegion, please try again or create manually. Exiting now."
                exit 1
            fi
        fi
        
        echo "...ensuring bucket lifecycle configuration is correct for ${requestBuckets[$key]}..."
        requestBucketLifeCycleConfigurationCurrent=$(aws s3api get-bucket-lifecycle-configuration --bucket ${requestBuckets[$key]} --region $useRegion --output json)
        if [ "$requestBucketLifeCycleConfiguration" == "$requestBucketLifeCycleConfigurationCurrent" ]; then
            echo "... ... lifecycle configuration is correct for ${requestBuckets[$key]}"
        else
            echo "... ... lifecycle configuration is NOT correct, configuring now..."
            requestBucketLifeCycleConfigurationCurrent=$(aws s3api put-bucket-lifecycle-configuration --bucket ${requestBuckets[$key]} --region $useRegion --lifecycle-configuration "$requestBucketLifeCycleConfiguration" --expected-bucket-owner "$accountId" --output json)
            echo "... ... ... now correctly configured"
        fi
        for functionName in *; do
            lambdaName="$lambdaNamespace-region-$functionName"
            echo "... ... ... checking if $lambdaName exists..."
            existingFunctionArn="$(aws lambda list-functions --region $useRegion --query "Functions[?FunctionName == '$lambdaName'].FunctionArn | [0]" --output text)"
            if [ "${#existingFunctionArn}" -ge 10 ]; then
                echo "... ... ... ... $lambdaName already exists."
            else
                echo "... ... ... ... $lambdaName NOT exists, creating now..."
                cd "$functionName/"
                if [ ! -d 'temp' ]; then
                    mkdir temp
                fi
                cp main.py ./temp
                cd temp
                sed -i "1s/.*/$lambdaEnvRegion/" main.py
                zip ../$functionName.zip main.py
                cd ../
                aws lambda create-function --function-name $lambdaName --runtime python3.8 --handler main.main --role $lambdaRoleArn --zip-file fileb://$functionName.zip --timeout 900 --publish --region $useRegion
                unlink temp/main.py
                rmdir temp
                unlink $functionName.zip
                cd ../
            fi
            if [ 'request' = $functionName ]; then
                echo "... ... ... ... checking if trigger from regional request bucket (${requestBuckets[$key]}) to request lambda ($lambdaName) exists..."
                getNotificationConfigurations=$(aws s3api get-bucket-notification-configuration --bucket ${requestBuckets[$key]} --query "LambdaFunctionConfigurations[?Id == '$functionName'].Id | [0]" --output text)
                if [ ! "$getNotificationConfigurations" == "$functionName" ]; then
                    echo "... ... ... ... ... ... .. NOT exists, creating now..."
                    notificationConfiguration='{"LambdaFunctionConfigurations": [{"Id": "'$functionName'", "LambdaFunctionArn": "arn:aws:lambda:'$useRegion':'$accountId:'function:'$lambdaName'","Events": ["s3:ObjectCreated:*"]}]}'
                    aws lambda add-permission --region $useRegion --function-name "arn:aws:lambda:$useRegion:$accountId:function:$lambdaName" --action "lambda:InvokeFunction" --statement-id "request" --principal "s3.amazonaws.com" --source-account "$accountId" --source-arn "arn:aws:s3:::${requestBuckets[$key]}"
                    aws s3api put-bucket-notification-configuration --bucket ${requestBuckets[$key]} --notification-configuration "$notificationConfiguration"
                    getNotificationConfigurations=$(aws s3api get-bucket-notification-configuration --bucket ${requestBuckets[$key]} --query "LambdaFunctionConfigurations[?Id == '$functionName'].Id | [0]" --output text)
                    if [ "$functionName" == "$getNotificationConfigurations" ]; then
                        echo "... ... ... ... ... ... trigger created."
                    else 
                        echo "... ... ... ... ... ... error creating trigger, please try again or create it manually: "
                        echo "Lambda Function: $lambdaName"
                        echo "Trigger Name: $functionName"
                        echo "Trigger Type: S3"
                        echo "Trigger Event: Any Object created"
                        echo "Bucket: ${requestBuckets[$key]}"
                        echo "... ... ... ... ... ... exiting now."
                        exit 1
                    fi
                else
                    echo "... ... ... ... ... already exists."
                fi
            fi
        done
done
cd ../
echo "
---------
"


echo "Ensuring API Gateway for websocket support is created and configured correctly..."
    echo "... checking if API Gateway ($websocketApiName) exists..."
    websocketApiId=$(aws apigatewayv2 --region $coreRegion get-apis --query "Items[?Name == '$websocketApiName'].ApiId | [0]" --output text) 
    if [ ${#websocketApiId} -le 6 ]; then
        echo "... ... NOT exists, creating now in coreRegion ($coreRegion)..."
        websocketApiId=$(aws apigatewayv2 create-api --region $coreRegion --name "$websocketApiName" --protocol-type 'WEBSOCKET' --route-selection-expression '$request.body.route' --query "ApiId" --output text)
        echo "... ... ... now created."
    fi
    websocketApiEndpoint=$(aws apigatewayv2 get-api --region $coreRegion --api-id "$websocketApiId" --query "ApiEndpoint" --output text)
    if [ ${#websocketApiEndpoint} -ge 10 ]; then
        echo "... ... API Gateway ($websocketApiName) exists with endpoint $websocketApiEndpoint, checking now for a stage named $websocketApiStageName..."
    else 
        echo "... ... ... error creating web socket API Gateway ($websocketApiName), please try again or create this API manually in the  $coreRegion region as follows:"
        echo "API Protocol: WEBSOCKET"
        echo "API Name: $websocketApiName"
        echo 'Route Selection Expression: $request.body.route'
        echo "... ... ... exiting now."
        exit 1
    fi
    echo "... checking if Lambda integration is configured..."
    websocketIntegrationUri="arn:aws:lambda:$coreRegion:$accountId:function:$lambdaNamespace-core-socket"
    websocketIntegrationPath="arn:aws:apigateway:$coreRegion:lambda:path/2015-03-31/functions/$websocketIntegrationUri/invocations"
    checkWebsocketApiIntegrationPath=$(aws apigatewayv2 get-integrations --region $coreRegion --api-id "$websocketApiId" --query "Items[?IntegrationUri == '$websocketIntegrationPath'].IntegrationUri | [0]" --output text)
    if [ "$checkWebsocketApiIntegrationUri" = "$websocketIntegrationPath" ]; then
        echo "... ... already exists."
    else
        echo "... ... NOT exists, creating now..."
        aws lambda add-permission --region $coreRegion --function-name "$websocketIntegrationUri" --action "lambda:InvokeFunction" --statement-id "websocket-connect" \
            --principal "apigateway.amazonaws.com" --source-arn 'arn:aws:execute-api:'$coreRegion':'$accountId':'$websocketApiId'/*/$connect'
        aws lambda add-permission --region $coreRegion --function-name "$websocketIntegrationUri" --action "lambda:InvokeFunction" --statement-id "websocket-disconnect" \
            --principal "apigateway.amazonaws.com" --source-arn 'arn:aws:execute-api:'$coreRegion':'$accountId':'$websocketApiId'/*/$disconnect'
        aws lambda add-permission --region $coreRegion --function-name "$websocketIntegrationUri" --action "lambda:InvokeFunction" --statement-id "websocket-default" \
            --principal "apigateway.amazonaws.com" --source-arn 'arn:aws:execute-api:'$coreRegion':'$accountId':'$websocketApiId'/*/$default'
        websocketApiIntegrationId=$(aws apigatewayv2 create-integration --region $coreRegion --api-id "$websocketApiId" --connection-type 'INTERNET' \
            --content-handling-strategy 'CONVERT_TO_TEXT' --integration-method 'POST' --integration-type 'AWS_PROXY' \
            --integration-uri "$websocketIntegrationPath" --passthrough-behavior 'WHEN_NO_MATCH' \
            --query "IntegrationId" --output text)
        aws apigatewayv2 create-route --region $coreRegion --api-id "$websocketApiId" --route-key '$connect' --target "integrations/$websocketApiIntegrationId"
        aws apigatewayv2 create-route --region $coreRegion --api-id "$websocketApiId" --route-key '$disconnect' --target "integrations/$websocketApiIntegrationId"
        aws apigatewayv2 create-route --region $coreRegion --api-id "$websocketApiId" --route-key '$default' --target "integrations/$websocketApiIntegrationId"
        if [ ${#websocketApiIntegrationId} -ge 5 ]; then
            echo "... ... now created."
        else
            echo "... ... error creating integration, please try again or create manually:"
            echo "From API: $websocketApiName"
            echo "To Lambda Function: $lambdaNamespace-core-socket"
            exit 1
        fi
    fi
    stageName=$(aws apigatewayv2 get-stage --region $coreRegion --api-id "$websocketApiId" --stage-name 'websocket' --query "StageName" --output text)
    if [ 'websocket' = "$stageName" ]; then
        echo "... ... ... already exists."
    else
        echo "... ... ... NOT exists, creating now..."
        stageName=$(aws apigatewayv2 create-stage --region $coreRegion --api-id "$websocketApiId" --stage-name 'websocket' --query "StageName" --output text)
        if [ 'websocket' = "$stageName" ]; then
            echo "... ... ... now created."
        else
            echo "... ... ... error creating stage ('websocket'), please try again or create manually. Exiting now."
            exit 1
        fi
    fi
    echo "... checking API deployment status..."
    deploymentStatus=$(aws apigatewayv2 get-deployments --region $coreRegion --api-id "$websocketApiId" --query "Items[?DeploymentStatus == 'DEPLOYED'].DeploymentStatus | [0]" --output text)
    if [ "DEPLOYED" = "$deploymentStatus" ]; then
        echo "... ...  already deployed."
    else 
        echo "... ...  NOT yet deployed, deploying now..."
        deploymentStatus=$(aws apigatewayv2 create-deployment --region $coreRegion --api-id "$websocketApiId" --stage-name 'websocket' --query "DeploymentStatus" --output text)
        if [ "DEPLOYED" = "$deploymentStatus" ]; then
            echo "... ... now deployed."
        else 
            echo "... ... error deploying API Gateway ($websocketApiName) to stage 'websocket, please try again to do this manually. Exiting now."
            exit 1
        fi
    fi


echo "Ensuring CloudFront distribution is created and configured correctly..."

    echo "... checking for origin access identity..."
    originAccessIdentityId=$(aws cloudfront list-cloud-front-origin-access-identities --query "CloudFrontOriginAccessIdentityList.Items[?Comment == '$systemProperName'].Id | [0]" --output text)
    if [ ${#originAccessIdentityId} -ge 10 ]; then
        echo "... ... already exists with Id $originAccessIdentityId."
    else
        echo "... ... NOT exists, creating now..."
        originAccessIdentityConfig='{
            "CallerReference": "'$systemProperName'",
            "Comment": "'$systemProperName'"
        }'
        aws cloudfront create-cloud-front-origin-access-identity --cloud-front-origin-access-identity-config "$originAccessIdentityConfig"
        originAccessIdentityId=$(aws cloudfront list-cloud-front-origin-access-identities --query "CloudFrontOriginAccessIdentityList.Items[?Comment == '$systemProperName'].Id | [0]" --output text)
        if [ ${#originAccessIdentityId} -ge 10 ]; then
            echo "... ... now created with Id $originAccessIdentityId."
        else
            echo "... ... ... error creating origin access identity, please try again. Exiting now..."
            exit 1
        fi
    fi
    
    echo "... ensuring coreBucket policy to allow Cloudfront access via the origin access identity ($originAccessIdentityId) is correct..."
    cloudfrontS3PolicyStatement='{
        "Effect": "Allow",
        "Principal": {
            "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity '$originAccessIdentityId'"
        },
        "Action": ["s3:GetObject","s3:PutObject","s3:DeleteObject"],
        "Resource": "arn:aws:s3:::'$coreBucket'/*"
    }'
    bucketPolicy='{
        "Statement": [
            '"$lambdaPolicyStatement"',
            '"$cloudfrontS3PolicyStatement"'
        ]
    }'
    aws s3api put-bucket-policy --bucket $coreBucket --policy "$bucketPolicy"
    echo "... ... Cloudfront access granted to $coreBucket."

    dCoreOrigin='{
        "Id": "'$coreBucket'",
        "DomainName": "'$coreBucket'.s3.'$coreRegion'.amazonaws.com",
        "OriginPath": "",
        "OriginShield": {
            "Enabled": false
        },
        "S3OriginConfig": {
            "OriginAccessIdentity": "origin-access-identity/cloudfront/'$originAccessIdentityId'"
        },
        "ConnectionAttempts": 3,
        "ConnectionTimeout": 10
    }'
    dErrorOrigin='{
        "Id": "'$coreBucket'-403",
        "DomainName": "'$coreBucket'.s3.'$coreRegion'.amazonaws.com",
        "OriginPath": "/'$envSystemRoot'/error/403.html",
        "OriginShield": {
            "Enabled": false
        },
        "S3OriginConfig": {
            "OriginAccessIdentity": "origin-access-identity/cloudfront/'$originAccessIdentityId'"
        },
        "ConnectionAttempts": 3,
        "ConnectionTimeout": 10
    }'
    dOrigins='{
        "Quantity": 2,
        "Items": ['$dCoreOrigin', '$dErrorOrigin']
    }'
    lambdaFunctionAssociations='{
        "Quantity": 1, 
        "Items": [
            {
                "LambdaFunctionARN": "arn:aws:lambda:'$edgeRegion':'$accountId':function:'$lambdaNamespace'-edge-accept:'$acceptFunctionVersion'", 
                "EventType": "origin-request", 
                "IncludeBody": true
            }
        ]
    }'
    
    echo "... checking to see if cache policy ${systemProperName}Standard exists..."
    dCachePolicyIdStandard=$(aws cloudfront list-cache-policies --type custom --query "CachePolicyList.Items[?CachePolicy.CachePolicyConfig.Name == '${systemProperName}Standard'] | [0].CachePolicy.Id" --output text)
    if [ ${#dCachePolicyIdStandard} -ge 10 ]; then
        echo "... ... already exists."
    else
        echo "... ... NOT exists, creating now..."
        dCachePolicyIdStandard=$(aws cloudfront create-cache-policy --cache-policy-config "$cachePolicyDocumentStandard" --query "CachePolicy.Id" --output text)
        if [ ${#dCachePolicyIdStandard} -ge 10 ]; then
            echo "... ... ... now created."        
        else
            echo "... ... ... error creating cache policy ${systemProperName}Standard, please try again or create it manually:"
            echo ""
        fi
    fi
    echo "... checking to see if cache policy ${systemProperName}Disabled exists..."
    dCachePolicyIdDisabled=$(aws cloudfront list-cache-policies --type custom --query "CachePolicyList.Items[?CachePolicy.CachePolicyConfig.Name == '${systemProperName}Disabled'] | [0].CachePolicy.Id" --output text)
    if [ ${#dCachePolicyIdDisabled} -ge 10 ]; then
        echo "... ... already exists."
    else
        echo "... ... NOT exists, creating now..."
        dCachePolicyIdDisabled=$(aws cloudfront create-cache-policy --cache-policy-config "$cachePolicyDocumentDisabled" --query "CachePolicy.Id" --output text)
        if [ ${#dCachePolicyIdDisabled} -ge 10 ]; then
            echo "... ... ... now created."        
        else
            echo "... ... ... error creating cache policy ${systemProperName}Disabled, please try again or create it manually:"
            echo ""
        fi
    fi
    echo "... checking to see if origin request policy ${systemProperName}Standard exists..."
    dOriginRequestPolicyIdStandard=$(aws cloudfront list-origin-request-policies --type custom --query "OriginRequestPolicyList.Items[?OriginRequestPolicy.OriginRequestPolicyConfig.Name == '${systemProperName}Standard'].OriginRequestPolicy.Id" --output text)
    if [ ${#dOriginRequestPolicyIdStandard} -ge 10 ]; then
        echo "... ... already exists."
    else
        echo "... ... NOT exists, creating now..."
        dOriginRequestPolicyIdStandard=$(aws cloudfront create-origin-request-policy --origin-request-policy-config "$originRequestPolicyStandard" --query "OriginRequestPolicy.Id" --output text)
        if [ ${#dOriginRequestPolicyIdStandard} -ge 10 ]; then
            echo "... ... ... now created."        
        else
            echo "... ... ... error creating origin request policy ${systemProperName}Standard, please try again or create it manually:"
            echo ""
        fi
    fi

    echo "... preparing distribution configuration..."
    defaultCacheBehaviour='{
        "TargetOriginId": "'$coreBucket'",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 3,
            "Items": ["GET", "HEAD", "OPTIONS"],
            "CachedMethods": {
                "Quantity": 3,
                "Items": ["GET", "HEAD", "OPTIONS"]
            }
        },
        "Compress": true,
        "CachePolicyId": "'$dCachePolicyIdStandard'",
        "OriginRequestPolicyId": "'$dOriginRequestPolicyIdStandard'"
    }'
    
    declare -A readBehaviour
    readBehaviour["TargetOriginId"]=$coreBucket
    readBehaviour["AllowedMethods"]='{
        "Quantity": 3,
        "Items": ["GET", "HEAD", "OPTIONS"],
        "CachedMethods": {
            "Quantity": 3,
            "Items": ["GET", "HEAD", "OPTIONS"]
        }
    }'
    readBehaviour["CachePolicyId"]=$dCachePolicyIdDisabled
    readBehaviour["OriginRequestPolicyId"]=$dOriginRequestPolicyIdStandard

    declare -A writeBehaviour
    writeBehaviour["TargetOriginId"]=$coreBucket
    writeBehaviour["AllowedMethods"]='{
        "Quantity": 7,
        "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
        "CachedMethods": {
            "Quantity": 3,
            "Items": ["GET", "HEAD", "OPTIONS"]
        }
    }'
    writeBehaviour["CachePolicyId"]=$dCachePolicyIdDisabled
    writeBehaviour["OriginRequestPolicyId"]=$dOriginRequestPolicyIdStandard

    declare -A blockedBehaviour
    blockedBehaviour["TargetOriginId"]=$coreBucket'-403'
    blockedBehaviour["AllowedMethods"]='{
        "Quantity": 7,
        "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
        "CachedMethods": {
            "Quantity": 3,
            "Items": ["GET", "HEAD", "OPTIONS"]
        }
    }'
    blockedBehaviour["CachePolicyId"]=$dCachePolicyIdStandard
    blockedBehaviour["OriginRequestPolicyId"]=$dOriginRequestPolicyIdStandard

    PathPatternOrder=(
        "$envSystemRoot/connection/????????-????-????-????-????????????/subscription/*/????????-????-????-????-????????????/*.*::r" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/subscription/*/????????-????-????-????-????????????.*::r" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/feed/*/????????-????-????-????-????????????/*/*/*/*-*.*::r" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/record/*/????????-????-????-????-????????????/*.json::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/record/*/????????-????-????-????-????????????.json::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/subscription/*/????????-????-????-????-????????????/????????-????-????-????-????????????.json::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/feed/*/????????-????-????-????-????????????/????????-????-????-????-????????????.json::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/query/*/????????-????-????-????-????????????.json::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/asset/*::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/static/*::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/view/????????-????-????-????-????????????.json::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/mask/????????-????-????-????-????????????.json::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/connect.json::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/system/*/*.json::w" 
        "$envSystemRoot/connection/????????-????-????-????-????????????/error/*.html::w" 
        "$envSystemRoot/*::b"
    )
    
    dCacheBehaviourItemsArray=()
    for key in ${PathPatternOrder[@]}; do 
        PathPattern="${key::-3}"
        behaviour="${key: -1}"
        if [ "$behaviour" == "r" ]; then
            TargetOriginId="${readBehaviour['TargetOriginId']}"
            AllowedMethods="${readBehaviour['AllowedMethods']}"
            LambdaFunctionAssociations="${readBehaviour['LambdaFunctionAssociations']}"
            CachePolicyId="${readBehaviour['CachePolicyId']}"
            OriginRequestPolicyId="${readBehaviour['OriginRequestPolicyId']}"
        fi
        if [ "$behaviour" == "w" ]; then
            TargetOriginId="${writeBehaviour['TargetOriginId']}"
            AllowedMethods="${writeBehaviour['AllowedMethods']}"
            LambdaFunctionAssociations="${writeBehaviour['LambdaFunctionAssociations']}"
            CachePolicyId="${writeBehaviour['CachePolicyId']}"
            OriginRequestPolicyId="${writeBehaviour['OriginRequestPolicyId']}"
        fi
        if [ "$behaviour" == "b" ]; then
            TargetOriginId="${blockedBehaviour['TargetOriginId']}"
            AllowedMethods="${blockedBehaviour['AllowedMethods']}"
            LambdaFunctionAssociations="${blockedBehaviour['LambdaFunctionAssociations']}"
            CachePolicyId="${blockedBehaviour['CachePolicyId']}"
            OriginRequestPolicyId="${blockedBehaviour['OriginRequestPolicyId']}"
        fi
        if [ "$behaviour" == "w" ]; then
            dCacheBehaviourItemsArray+='{
                "PathPattern": "'$PathPattern'",
                "TargetOriginId": "'$TargetOriginId'",
                "ViewerProtocolPolicy": "redirect-to-https",
                "AllowedMethods": '$AllowedMethods',
                "Compress": true,
                "LambdaFunctionAssociations": '$lambdaFunctionAssociations',
                "CachePolicyId": "'$CachePolicyId'",
                "OriginRequestPolicyId": "'$OriginRequestPolicyId'"
            }, '
        else 
            dCacheBehaviourItemsArray+='{
                "PathPattern": "'$PathPattern'",
                "TargetOriginId": "'$TargetOriginId'",
                "ViewerProtocolPolicy": "redirect-to-https",
                "AllowedMethods": '$AllowedMethods',
                "Compress": true,
                "CachePolicyId": "'$CachePolicyId'",
                "OriginRequestPolicyId": "'$OriginRequestPolicyId'"
            }, '
        fi
    done
    dCacheBehaviourItems="[${dCacheBehaviourItemsArray::-2}]"
    dCacheBehaviours='{
        "Quantity": 15, 
        "Items": '$dCacheBehaviourItems'
    }'
    
    dCustomErrorResponses='{
        "Quantity": 1, 
        "Items": [
            {
                "ErrorCode": 403, 
                "ResponsePagePath": "/'$envSystemRoot'/error/403.html", 
                "ResponseCode": "403", 
                "ErrorCachingMinTTL": 10
            }
        ]
    }'
    
    dLogging='{
        "Enabled": true, 
        "IncludeCookies": true, 
        "Bucket": "'$logBucket'.s3.amazonaws.com", 
        "Prefix": "cloudfront/'$systemProperName'/"
    }'
    
    distributionConfig='{
        "CallerReference": "'$systemProperName'", 
        "DefaultRootObject": "index.html", 
        "Origins": '$dOrigins', 
        "DefaultCacheBehavior": '$defaultCacheBehaviour', 
         "CacheBehaviors": '$dCacheBehaviours', 
        "CustomErrorResponses": '$dCustomErrorResponses',  
        "Comment": "'$systemProperName'", 
        "Logging": '$dLogging', 
        "PriceClass": "PriceClass_All", 
        "Enabled": true, 
        "ViewerCertificate": {
            "CloudFrontDefaultCertificate": true
        }, 
        "IsIPV6Enabled": true
    }'
    
    echo "... checking if the distribution $systemProperName exists..."
    cloudfrontDistributionId=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment == '${systemProperName}'].Id | [0]" --output text)
    if [ "${#cloudfrontDistributionId}" -ge 10 ]; then
        echo "... already exists."
    else 
        echo "... not exists, creating now..."
        cloudfrontDistributionId=$(aws cloudfront create-distribution --query "Distribution.Id" --distribution-config "$distributionConfig" --output text)
        if [ "${#cloudfrontDistributionId}" -ge 10 ]; then
            echo "... distribution created."
        else 
            echo "... error creating distribution ${systemProperName}, please retry or create manually:"
            echo "Cloudfront distribution JSON set up configuration: "
            echo ".. exiting now."
            exit 1
        fi
    fi
    
    echo "... confirming your Cloudfront distribution URL: "
    distributionURL=$(aws cloudfront get-distribution --id "$cloudfrontDistributionId" --query "Distribution.DomainName" --output text)
    echo "
    
    $distributionURL
    
    "
echo "
---------
"


if [ "$envShared" == "0" ]; then
    echo "Dedicated installation, running system configuration processes...."
    echo "... installing datatypes from schema.org..."
    schemaStatusCode=$(aws lambda invoke --region $coreRegion --function-name "arn:aws:lambda:$coreRegion:$accountId:function:$lambdaNamespace-core-schema" --invocation-type "Event" --log-type "Tail" --payload '{}' --query "StatusCode" --output text /tmp/schema.log)
    if [ "202" == "$schemaStatusCode" ]; then
        echo "... datatype installation underway, will continue in the background and may take up to 15 minutes to complete."
    else
        echo "... error with datatype installation. Please try again or complete manually by running the $lambdaNamespace-core-schema Lambda function (no payload required)."
    fi
    
    echo "... initialisation the system, including adding the sudo user..."
    sudoKey=$(uuidgen)
    initialisePayload='{"key": "'$sudoKey'", "name": "'$sudoName'", "_env": {"bucket": "'$coreBucket'", "lambda_namespace": "'$lambdaNamespace'", "data_root": "'$envSystemRoot'"}}'
    initialiseStatus=$(aws lambda invoke --region $coreRegion --function-name "arn:aws:lambda:$coreRegion:$accountId:function:$lambdaNamespace-core-initialise" --invocation-type "RequestResponse" --log-type "Tail" --payload "$initialisePayload" --query "StatusCode" --output text /tmp/initialise.log)
    if [ "200" == "$initialiseStatus" ]; then
        echo "system initialisation complete, sudo user added"
        echo "Sudo user name: $sudoName"
        echo "Your sudo key is: " 
        echo ""
        echo "$sudoKey"
        echo ""
        echo "Copy it now as it will not be displayed again"
    else
        echo "... error initialising the system and / or creating the sudo user, please retry or complete manually:"
        echo ""
        echo "Lambda Function: $lambdaNamespace-core-schema"
        echo "Payload: "
        echo '{
            "key": "'$sudoKey'", 
            "name": "'$sudoName'", 
            "_env": {
                "bucket": "'$coreBucket'", 
                "lambda_namespace": "'$lambdaNamespace'", 
                "data_root": "'$envSystemRoot'"
            }
        }'
        echo ""
        echo "... exiting now..."
        exit 1
    fi
    echo "... configuration processes for dedicated installation complete (except for continuing background processes if indicated)."
fi
echo "
---------
"


echo "LiveElement Scale installation complete on $coreBucket"
echo "

---------
---------

"
exit 0
