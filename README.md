# Scale
Serve real-time structured data to millions of concurrent users at the lowest possible cost. Part of 
the [live-element](https://live-element.net) framework.


## What It Is 
**LiveElement Scale is intended to be a complete backend stack for your PWA web app.** It can serve up your static assets, 
application files and structured data from one AWS S3 bucket, all delivered via CDN over simple HTTPS connections that's as 
easy as a Javascript `fetch` request. Together with the other LiveElement modules, it is all you need to create an 
advanced, scalable, economical, high performance Progressive Web App. It is also extensible, with the ability to create new 
authentication types, query functions, permission masks, and data presentation views in any backend language of your 
choice (although Python is optimal for speed and cost)


## What It Can Do
* be an application server for one or more client apps, serving both static and dynamic assets and data
* handle complex authentication, you can use any Lambda function you like to handle the process of accepting 
authentication data and assigning attributes and permissions to a connection
* handle complex authorisation, write any Lambda function to create an inheritable permissions structure to allow/deny 
data and file access down to a per-record-field granularity
* handle complex data queries, write and Lambda function to create complex pre-compiled queries over your data records
* 850+ record types built-in (everything from [schema.org](https://schema.org/)), you can extend this with your own 
record types anytime
* create data views which can present your record and query data in any format you like, served as static files over 
a CDN
* host multiple separate independent databases and file structures under subdomains of one domain


## What It Should NOT Be Asked To Do
* Act as the database / datastore for an application which requires guaranteed transaction integrity. This is an 
**eventually-consistent** system with a delay between writes and updates being pushed out to all client connections. 
* Try to serve multiple databases of different primary domains - there is a restriction in Cloudfront which will prevent
this (would love to hear about any known workarounds that make this possible). At the moment you can only partition
different systems on different subdomains under the same root domain.


## Installation 
At this point (release 0.5) Scale is architected for AWS only. It installs as a set of Lambda functions, S3 buckets, 
IAM policies and Cloudfront distributions on your AWS account.

To install you basically just clone this repository, configure the `./vars` file, and then run `./setup.sh` on your 
terminal (make sure you `chmod +x ./setup.sh` first so that it's executable). Your terminal has to have your AWS 
credentials available in it's environment.

The way it has been developed and tested has been by created a Cloud9 IDE instance, cloning the repository onto that and 
running from there. The Cloud9 instance has all the permissions and credential in it's environment that is needed for the 
process to run smoothly.

The `./setup.sh` script is designed to be idempotent - if installation fails part way, just re-run it to try again without 
any harmful sideeffects. It will take you if it encounters a fatal error and give you basic instructions to manually do 
that step so you can re-run and have it pick up where you left off.

At the end of a successful installation, you will be presented with the Cloudfront URL of your installation, plus the 
sudo key. The sudo key is not stored anywhere so you must copy it and store it safely at the point.

If you run `./setup.sh` on an already installed system it will change the sudo user key - otherwise it is a safe 
operation. Doing this is a way to recover the sudo key if you have lost it. 


## Installation Configuration via `vars`
You must personalise the values of line 3-13 in `vars` to your own requirements as follows before running `setup.sh`

```
accountId="000000000000"
systemProperName="ExampleLiveElementScale"
lambdaNamespace="exampleliveelement-scale"
coreBucket="example.scale.live-element.net"
coreRegion="ap-southeast-1"
edgeRegion="us-east-1"
logBucket="log.example.scale.live-element.net"
requestBucket="request.example.scale.live-element.net"
envSystemRoot="_"
envShared="0"
sudoName="system"
```

* **accountId**: the 10 digit numeric id of your AWS account
* **systemProperName**: the name for you installation, used for policy and role names and more through out
* **lambdaNamespace**: the prefix to use when naming your Lambda functions, should be lowercase or - , and maximum 25 characters
* **coreBucket**: the full name of the bucket that you want to use for serving your data and files from. Will be created 
if not already existing. 
* **coreRegion**: the AWS region that the core data and processing will happen and be stored in
* **edgeRegion**: at this point must be `us-east-1`, as required by AWS for Lambda@Edge functions
* **logBucket**: the full name of the bucket to use for logging, will be created if not already existing
* **requestBucket**: the full name of the bucket to use for caching requests, will be created if not already existing
* **envSystemRoot**: a short prefix that will be used for data and system files within the coreBucket
* **envShared**: `"0"` if this system is a dedicated installation for one database, or `"1"` if this will be configured to 
serve multiple databases from one bucket
* **sudoName**: the user name of the system administrator user 

Lines in `vars` after 13 can be adjusted if you wish, however you should not do this unless you know exactly why and 
what you are doing!


## Basic Usage
Simple examples to get an idea of the basics...

### Authenticate: 

```
fetch(
    'https://{your-cloudfront-url}/_/connection/{a-generated-uuid-of-your-choice}/connect.json', 
    {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(
        {sudo: {key: "{your sudo key uuid as given at the end of setup.sh}"}}
    ) }
).then(r => console.log(r))

```

Grants you complete access to the system as a super user, to connect as a non-super user you need to define other 
authentication processors in extensions/authentication/*


### PUT a record:

```
fetch(
    'https://{your-cloudfron-url}/_/connection/{your-connection-uuid}/record/Book/{generate-your-own-record-uuid}.json', 
    {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(
        {"@type": "Book", "@id": "{the same record-uuid as in the url}", "name": "Test Book", "numberOfPages": 10}
    ) }
).then(r => console.log(r))

```
Creates or updates the record of the given type (Book).


### PUT a single record field:

```
fetch(
    'https://{your-cloudfront-url}/_/connection/{connection-uuid}/record/Book/{record-uuid}/numberOfPages.json', 
    {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(
        11
    ) }
).then(r => console.log(r))

```
Updates the record's `numberOfPages` field with the new value of `11`.


### PUT a view (a definition for how you want the data to be presented, once per app deployment):
```
fetch(
    'https://{your-cloudfront-url}/_/connection/{connection-id}/view/{generated-uuid}.json', 
    {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(
        {"processor": "json", "content_type": "application/json", "suffix": "json"}
    ) }
).then(r => console.log(r))

```
The `processor` field of the view will refer to a Lambda function at extensions/view/json, this one is built-in and renders 
records in JSON format. This view is now defined and ready for use by any records subscriptions in perpetuity.


### PUT a subscription to the record (lets the system know that you want to keep track of this record, once per connection):
```
fetch(
    'https://{your-cloudfront-url}/_/connection/{your-connection-uuid}/subscription/Book/{record-uuid}/{generate-your-own-subscription-uuid}.json', 
    {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(
        {"view": "{the generated uuid that you used for the view above}"}
    ) }
).then(r => console.log(r))

```
The system now knows that this connection wants to have access to this record, rendered using the given view.


### GET record subscription
```
fetch('https://{your-cloudfront-url}/_/connection/{connection-uuid}/subscription/Book/{record-uuid}.json').then(r => r.json()).then(r => console.log(r))

```
The browser gets the rendered version of the record. Updates to the record will be automatically propgated to this endpoint 
as they are received, if you want live updates simply poll this endpoint, it is not cached. Near-future versions will 
include an extension to allow for updates to websocket connections.


## Bucket Structure

All files and data live within one bucket (your `coreBucket`). Another bucket within the same region to cache write requests
for processing. In each edge region that you want to support faster writes for, a request bucket is create to cache write
requests from that region. All cached write requests are automatically deleted after 24 hours. 

There is also a separate `logBucket` in the same region as the `coreBucket` to which all system activity logs are written. 


## File Structure within the `coreBucket`

All your files and data live within this bucket. You specify a `system_root` prefix to tell the system where to place the 
structured data files and any permission protected blob assets. Any files outside of this prefix will be publically 
accessible and aggressively cached by the CDN.


## Lambda Structure

All core lambda functions live in the same region as your core bucket. There is a one Lambda@Edge function which will be 
deployed in the `us-east-1` region and handles write requests directed to the Cloudfront endpoint. In addition, if you
enable regional write buckets, a lambda function will be deployed in each supported region to handle request processing 
from that region.


## Reguest Flow

### Write Requests

1: You write a record or other data to your Cloudfront endpoint with a PUT/POST/DELETE request. 

2: Your request is cached in the closest regional bucket and returns a HTTP 202 Accepted status.

3: The regional Lambda request processor picks up the request, validates it and writes the validated request to your 
core `requestBucket`

4: The core request Lambda 
  








 

## Further Reading 

[live-element framework](https://live-element.net)

[Data Types at Schema.org](https://schema.org)

[AWS](https://aws.amazon.com)


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
