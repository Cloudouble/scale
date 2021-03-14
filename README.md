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

2: Your request is cached in the closest regional bucket by the edge/accept Lambda and returns a HTTP 202 Accepted status, 
normally within 100ms.

3: The regional copy of the region/request processor picks up the request asynchronously, validates it and writes the 
validated request to your core `requestBucket`

4: The core/request Lambda picks up the request asynchronously, checks permissions and writes the permissioned result 
to the core bucket as a record or other object.


### Update Processing

Depending on the object type (a record, an asset, or a configuration for a view/query/subscription etc), one of the trigger 
Lambdas picks up the object and responds to it. The main process is the response to a record update, which will be 
detailed here.
  
1: When a record is written to the bucket, a version object is created recording what record fields were changed in that 
update. 

2: The trigger/version Lambda responds to the new version object and finds any queries that query based on one of the 
fields changed in this version.

3: Each query is run (asynchronously in parallel) with the single record. The query index is updated if neccessary. It's
important to note a query does not run over the entire record set, but only on each updated record as a relevant field
is updated. This architectural feature is what keeps the system scalable.

4: Also from step 2, any subscriptions interested in this record are checked and a permissioned version of this record 
is written into the record cache for subscribed connections. 

5: From step 3, any feeds interested in updates to this query are checked and a permissioned version of this query index 
is written / updated in the query cache for interested connections.

6: If changes are detected in the permissioned versions of the record or query result, results are rendered according 
to the configured view and made available to the connection.

The timeline from initial write to the updated view being made available is generally 5-10 seconds, and will NOT increase 
according to the size of database or numbers of connections, in fact it should get slightly faster as the system gets 
busier.

Actual read and write HTTP requests are always via the CDN, so should always be less than 100ms.


# Authentication

*In this and following sections the url is presented as the path within your Cloudfront URL endpoint. Your `system_root` as 
configured during installation is shown as the its default value of "_". Any instance of `$uuid-***` represents a Version 4 UUID
generated by the connecting client. The name of the bucket containing your data is shown as `$coreBucket`.*

The authentication approach is to define a connection, identified by a client-generated version 4 UUID, and then upgrade
it by sending an authentication payload to the `connect.json` endpoint as detailed in the "API Endpoints" section.

The structure of the request body will be determined by the requirements of the active authentication extensions, by 
default at installation only the "sudo" authentication extension is installed and active, and it requires the structure of: 

`{sudo: {key: "$uuid-sudo-key"}}`

Where `$uuid-sudo-key` is the "sudo key" passed back at the end of the install process. This upgrades a connection to 
super-user permissions.

This super-user access can be completely disabled by deleting the file in at 
`s3://$coreBucket/_/system/authentication/sudo.json` . To reenable sudo access, either put that exact file back, or re-run the
setup process (which will re-instate the sudo authentication extension with a new sudo key).

All paths under the `system_root` require a connection UUID (`$uuid-connection`), this can be supplied as: 

1: part of the path: e.g. `_/connection/$uuid-connection/subscription/Book/{$uuid-record}.json`

2: as the username part Basic Authorization header (use an empty password)

3: as the value of a "`$envAuthenticationNamespace`Connection" header 

4: as the value of a "`$envAuthenticationNamespace`Connection" cookie

In the case of options 2, 3 or 4, then the path will be simplified to `_/subscription/Book/{$uuid-record}.json`

To sign out, you DELETE to the `connect.json` endpoint, this will remove all cached / pre-complied connection data and reset 
its permissions to a public / unauthenticated status.


## API Endpoints

The `Content-Type` of the request body can be either `application/json`, or `application/x-www-form-urlencoded`. 

### `connect`

* **`_/connection/$uuid-connection/connect.json`**: `{...authentication request body dependent on active authentication extensions}`

Establish a connection potentially allowing access to protected data. `PUT`/`POST` to create or update, `DELETE` to remove.


### `system`

* **`PUT _/connection/$uuid-connection/system/{scope}/{module}.json`**: `{...system module configuration...}`
 
Create or update the configuration for any system module. for example to update the sudo authentication extension: 

`PUT _/connection/$uuid-connection/system/authentication/sudo.json`

Request body: 

`
{
  "processor": "sudo",
  "options": {
    "name": "system",
    "key": "sha512 hash of the sudo key"
  }
}
`

The value of "scope" may be one of `authentication`, `query`, `mask`, or `view`.

`PUT`/`POST` to create or update, `DELETE` to remove.


### `error`

* **`_/connection/$uuid-connection/error/{code}.html`**: `html of custom error page`

Create or update a custom error page for the given HTTP error code.

`PUT`/`POST` to create or update, `DELETE` to remove.


### `static`

* **`_/connection/$uuid-connection/static/{path}`**: `base64 encoded bytes of static asset`

Upload a binary / text asset to the unprotected areas outside of the `system_root`. These will be available to 
public connections without authentication and cached via the CDN. For example: 

`PUT _/connection/$uuid-connection/static/pixel.png`: `iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mNMN27/z0AEYBxVSF+FAIOrFUtBFtYjAAAAAElFTkSuQmCC`

Makes a single pixel PNG image available to anyone who goes to  `https://{your cloudfront url}/pixel.png`

`PUT`/`POST` to create or update, `DELETE` to remove.
 

### `asset`

* **`_/connection/$uuid-connection/asset/{path}`**: `base64 encoded bytes of static asset`

Upload a binary / text asset to the protected areas within the `system_root`. These will be available to 
authenticated connections and can be permissioned down to any sub-path level. For example: 

`PUT _/connection/$uuid-connection/asset/pixel.png`: `iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mNMN27/z0AEYBxVSF+FAIOrFUtBFtYjAAAAAElFTkSuQmCC`

Makes a single pixel PNG image available to authorised connections at  `https://{your cloudfront url}/_/asset/pixel.png`

`PUT`/`POST` to create or update, `DELETE` to remove.
 

### `view`

* **`_/connection/$uuid-connection/view/$uuid-view.json`**: `{view configuration}`

Defines a view which can be used by subscriptions and feeds to render records and queries. `PUT`/`POST` to create or update, `DELETE` to remove.


### `query`

* **`_/connection/$uuid-connection/query/{record type}/{$uuid-query}.json`**: `{query configuration}`

Defines a query used to filter, group and analyse records.  `PUT`/`POST` to create or update, `DELETE` to remove.


### `reccord`

* **`_/connection/$uuid-connection/record/{record type}/{$uuid-recrd}.json`**: `{"@type": "{the same record type as in the path}", "@id": "{the same client generated UUID as in the path}", .... other fields valid for the record type...}`

Creates or updates a record.  `PUT`/`POST` to create or update, `DELETE` to remove.


### `record/field`

* **`_/connection/$uuid-connection/record/{record type}/$uuid-record/{field name}.json`**: `the JSON encoded new value of the field`

Updates the value of a record field. `PUT`/`POST` to update, `DELETE` to remove (set to `undefined`).


### `feed`

* **`_/connection/$uuid-connection/feed/{record type}/$uuid-query/$uuid-feed.json`**: `{feed configuration}`

Updates or creates a feed definition, which allows a connection to receive updates to the result of a query and render views of it.

`PUT`/`POST` to create or update, `DELETE` to remove.


### `subscription`

* **`_/connection/$uuid-connection/subscription/{record type}/$uuid-record/$uuid-subscription.json`**: `{subscription configuration}`

Updates or creates a subscription definition, which allows a connection to receive update to the value of record and render views of it.

`PUT`/`POST` to create or update, `DELETE` to remove.
  

### `feed view`

* **`_/connection/$uuid-connection/feed/{record type}/$uuid-query/{render field}/{sort field}/{sort direction}/{min index}-{max index}.{view suffix}`**

`GET` only, get the data of a query, as rendered by the view and parameters as follows: 

* `render field`: the field of the queried records to render, or '-' to render the whole record
* `sort field`: the field of the queried records to sort the query results by
* `sort direction`: either 'ascending' or 'descending'
* `min index`: the first record to include in this rendering, starting from 0 for the first first as sorted by the sort field and direction
* `max index`: the index after the index of the last record to include this rendering
* `view suffix`: used to decide which view to use to render this query with, if multiple feeds are defined for this connection, query and suffix, the 
outcome is unpredictable (as of release 0.5), try not to do that

For example: 

`GET _/connection/$uuid-connection/feed/Book/$uuid-query/-/name/ascending/0-1000.json`

This will get all fields of the first 1000 Book records, as sorted ascending by name, as rendered by the view with a feed configured for this connection 
and the suffix of `json`. 


### `subscription view`

* **`_/connection/$uuid-connection/subscription/{record type}/$uuid-record.{view suffix}`** 

`GET` only, get the specified record, as rendered by the view with a subscription by this connection and the given suffix.


### `subscription field view`

* **`_/connection/$uuid-connection/subscription/{record type}/$uuid-record/{field name}.{view suffix}`**

`GET` only, get the specified record field, as rendered by the view with a subscription by this connection and the given suffix.


## Entity Types

### `connection`

`{"mask": {}, "name": "", ... }`

This entity lives at `_/connection/$uuid-connection/connect.json` and defined the permission and user name (and other fields 
are defined and use by your authentication extensions) for the given connection. 


### `view`

`{"processor": "", "options": {}, "assets": {"alias": "", ... }, "field_name": "", "content_type": "", "suffix": "", "expires": 0, "sort_field": "", "sort_direction": "", "min_index": 0, "max_index": 0}`

* `processor`: the name of a Lambda function that lives within the `$lambdaNamespace-extension-view-` namespace, without that prefix. 
For example the value of `json` here will look for `$lambdaNamespace-extension-view-json` to process the view

* `options`: a free dictionary of options which are passed to the view processor, this allows one processor to be used for 
multiple views

* `assets`: a dictionary of assets that should be present in the `_/asset/*` path which are passed to the processor, each passed 
with the given alias which loads the asset from the path value of the alias key. Good for loading templates for view 
rendering, or images to use within the rendering process

* `field_name`: the name of a record field, if the view should only be processing the data from that field, instead of the whole record

* `content_type`: the content_type to assign to the rendered object when accessed by a connection. e.g. 'application/json' or 'text/html'

* `suffix`: the path suffix to use for matching to view paths, should be related to the content type, e.g. 'json' or 'html'

* `expires`': a default timestamp for when feeds or subscriptions using this view should be discarded

* `sort_field`: a default sort_field value to assign when this view is used in a feed configuration

* `sort_direction`: a default sort_direction value to assign when this view is used in a feed configuration

* `min_index`: a default min_index value to assign when this view is used in a feed configuration

* `max_index`: a default max_index value to assign when this view is used in a feed configuration


### `query`

`{processor='', ?options={}, vector=[], ?count=0}`

* `processor`: the name of a Lambda function that lives within the `$lambdaNamespace-extension-query-`namespace, without that prefix. This
function will be used to process this query.

* `options`: a free dictionary or options to pass to the processor, this allows one processor to be used for multiple queries.

* `vector`: a list of record fields that this query is interested in, that is the query will only update when a member record changes the 
value of one of these fields.


### `feed`

`{view='', processor='', ?options={}, ?assets={alias: assetpath}, ?field_name='', ?content_type='', ?suffix='', ?expires=0, ?sort_field='', ?sort_direction='', ?min_index=0, ?max_index=0}`

* `view`: the $uuid of the view configuration to use for rendering this feed

... the other parameters are optional and can be used to override the same parameters as defined in the view 


### `subscription`

`{view='', processor='', ?options={}, ?assets={alias: assetpath}, ?field_name='', ?content_type='', ?suffix='', ?expires=0}`

* `view`: the $uuid of the view configuration to use for rendering this subscription

... the other parameters are optional and can be used to override the same parameters as defined in the view 


### `system`

`{}`

... the structure of these records is free and will vary depending on the target module itself. 


### `record`

`{@type, @id,  ...as per various schemas conforming to it's own @type... }`

* `@type`: the record type as defined in the system schema, must be the same as the `{record type}` component of the path.
 
* `@id`: a unique version UUID in the format '[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{}4-[a-z0-9]{4}-[a-z0-9]{12}', must be the 
same as the `$uuid-record` component of the path.


## Permissions

Scale uses a concept of "masks" to handle permissions. Any higher level abstractions such as groups, roles, privileges etc 
can be constructed based on the "mask" foundation and installed into the system by creating the relevant Lambda function 
within the namespace `$lambdaNamespace-extension-mask-`. This section will cover how a mask is defined for a connection.

The current mask for a connection is stored as the value of the mask key within `_/connection/$uuid-connection/connect.json`.

Here's some simple examples: 

`{"*": "*"}` => all permissions, can read, write and delete anything entity within the system

`{"record": "*"}` => can do anything with any record, can not do anything else

`{"record": {"GET": "*"}}` => can GET (view) any record, can not write to them

`{"record": {"GET": {"Book": "*"}}}` => can GET (view) any Book record, can not view other record types

`{"record": {"GET": {"Book": {"mask-function-id-1": {"options1": 1}, "mask-function-2": {"option2": 234}}}}}`  => the allowfields of 
mask-function-1 and mask-function-2 will be used to determine which fields of Book record the connection can GET (view). 
The rendering records of type "Book" for this connection, the two Lambda functions (which must be present in `$lambdaNamespace-extension-mask-`)
will be called with the connection's details and the given options and their output will be the allowfields for the records as made available 
to this connection. This technique can be used for granular per-record-type-and-field level permissions based on the dynamic
state of the connection itself. 

`{"asset": {"GET": {"file.png": "*"} } }` => can view _/asset/file.png

`{"asset": {"GET": {"profiles/": "*"} } }`   => can view any file under the _/profiles/ path

`{"asset": {"GET": {"profiles/": {"testuser.png": "*"} } } }`  => cam view the file _/profiles/testuser.png

`{"asset": {"GET": {"profiles/": {"testuser.png": {"mask-function-id": {"option1": 123}}}}}}`  => if the result of mask-function-id is true, 
then can view _/profiles/testuser.png

The mask itself is set by your active authentication extensions at the time of connection authentication. To change the mask on the fly, 
re-run the authentication process for the connection. To make an authentication extension active, use the `_/connection/$uuid-connection/system/*`
endpoint to PUT it's configuration to `_/system/authentication/{custom-authentication-name}.json` and write it's extension Lambda function as name it under the 
namespace `$lambdaNamespace-extension-authentication-{custom-authentication-name}`


# Writing Extensions 


## Authentication

As mentioned above, to make a new authentication extension active, use the `_/connection/$uuid-connection/system/*`
endpoint to PUT it's configuration to `_/system/authentication/{custom-authentication-name}.json` and write it's extension Lambda function as name it under the 
namespace `$lambdaNamespace-extension-authentication-{custom-authentication-name}`. This section explains how to write the Lambda function, the 
structure of the configuration file will be dependent on how your custom Lambda function processes its own configuration.











 

## Further Reading 

[live-element framework](https://live-element.net)

[Data Types at Schema.org](https://schema.org)

[AWS](https://aws.amazon.com)


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
