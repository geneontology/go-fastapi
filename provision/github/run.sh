#!/usr/bin/env bash

ansible --version
terraform --version
ls -l /tmp

# Prepare TF backend

s3_terraform_backend=$S3_TF_BACKEND
sed "s/REPLACE_ME_GOAPI_S3_STATE_STORE/$s3_terraform_backend/g" ./github/backend.tf.sample > aws/backend.tf

# Prepare config yaml files.
zone_id=`aws route53 list-hosted-zones-by-name --dns-name geneontology.io. --max-items 1  --query "HostedZones[].Id" --output text  | tr "/" " " | awk '{ print $2 }'`
record_name=cicd-test-go-fastapi.geneontology.io

check_record() {
    aws route53 list-resource-record-sets --hosted-zone-id $zone_id --max-items 1000 --query "ResourceRecordSets[?Name == '$record_name'] | [0].Name" --output text
    return $?
}

delete_record() {
    record_set=$(aws route53 list-resource-record-sets --hosted-zone-id $zone_id --query "ResourceRecordSets[?Name == '$record_name']" --output json)

    if [ -z "$record_set" ]; then
        echo "Record not found, nothing to delete."
        return 1
    else
      # Destroy
      go-deploy --working-directory aws -w test-go-deploy-api -destroy -verbose
      rm -f ./github/config-instance.yaml ./github/config-stack.yaml openapi.json
      exit $ret
    fi
}

# Initial check for the record
check_record
ret=$?

if [ "${ret}" == 0 ]; then
    echo "$record_name exists. Attempting to delete."
    delete_record
    del_ret=$?

    if [ "${del_ret}" == 0 ]; then
        echo "Successfully deleted $record_name. Trying again."
        check_record
        ret=$?

        if [ "${ret}" == 0 ]; then
            echo "$record_name still exists after deletion attempt. Cannot proceed."
        else
            echo "$record_name does not exist. Proceeding."
        fi
    else
        echo "Failed to delete $record_name. Cannot proceed."
    fi
else
    echo "$record_name does not exist. Proceeding."
fi

sed "s/REPLACE_ME_WITH_ZONE_ID/$zone_id/g" ./github/config-instance.yaml.sample > ./github/config-instance.yaml
sed -i "s/REPLACE_ME_WITH_RECORD_NAME/$record_name/g" ./github/config-instance.yaml

s3_cert_bucket=$S3_CERT_BUCKET
ssl_certs="s3:\/\/$s3_cert_bucket\/geneontology.io.tar.gz"
sed "s/REPLACE_ME_WITH_URI/$ssl_certs/g" ./github/config-stack.yaml.sample > ./github/config-stack.yaml
sed -i "s/REPLACE_ME_WITH_RECORD_NAME/$record_name/g" ./github/config-stack.yaml

# Provision aws instance and fast-api stack.

go-deploy -init --working-directory aws -verbose

go-deploy --working-directory aws -w test-go-deploy-api -c ./github/config-instance.yaml -verbose

go-deploy --working-directory aws -w test-go-deploy-api -output -verbose

go-deploy --working-directory aws -w test-go-deploy-api -c ./github/config-stack.yaml -verbose

ret=1
total=${NUM_OF_RETRIES:=100}


for (( c=1; c<=$total; c++ ))
do
   echo wget --https-only --no-dns-cache http://$record_name/openapi.json
   wget --https-only --no-dns-cache http://$record_name/openapi.json
   ret=$?
   if [ "${ret}" == 0 ]
   then
        echo "Success"
        break
   fi
   echo "Got exit_code=$ret.Going to sleep. Will retry.attempt=$c:total=$total"
   sleep 10
done

if [ "${ret}" == 0 ]
then
   echo "Parsing json file openapi.json ...."
   python3 -c "import json;fp=open('openapi.json');json.load(fp)"
   ret=$?
fi

# Destroy
go-deploy --working-directory aws -w test-go-deploy-api -destroy -verbose
rm -f ./github/config-instance.yaml ./github/config-stack.yaml openapi.json
exit $ret 
