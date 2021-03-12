# Scale
Serve real-time structured data to millions of concurrent users at the lowest possible cost. Part of 
the [live-element](https://live-element.net) framework.


## What It Is 
LiveElement Scale is intended to be a complete backend stack for your PWA web app. It can serve up your static assets, 
application files and structured data from one AWS S3 bucket, all delivered via CDN over simple HTTPS connections that's as 
easy as a Javascript `fetch` request. Together with the other LiveElement modules, it is all you need to create an 
advanced, scalable, economical, high performance Progressive Web App. It is also extensible, with the ability to create new 
authentication types, query functions, permission masks, and data presentation views in any backend language of your 
choice (although Python is optimal for speed and cost)


## Installation 
At this point (release 0.5) Scale is architected for AWS only. It installs as a set of Lambda functions, S3 buckets, 
IAM policies and Cloudfront distributions on your AWS account.

To install you basically just clone this repository and then run `./setup.sh` on your terminal (make sure you 
`chmod +x ./setup.sh` first so that it's executable). Your terminal has to have your AWS credentials available in it's 
environment.

The way it has been developed and tested has been by created a Cloud9 IDE instance, cloning the repository onto that and 
running from there. The Cloud9 instance has all the permissions and credential in it's environment that is needed for the 
process to run smoothly.

The `./setup.sh` script is designed to be idempotent - if installation fails part way, just re-run it to try again without 
any harmful sideeffects. It will take you if it encounters a fatal error and give you basic instructions to manually do 
that step so you can re-run and have it pick up where you left off.

If you run `./setup.sh` on an already installed system it will change the sudo user key - otherwise it is a safe operation.


## Usage
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
as they are received, if you want live updates simply poll this endpoint, it is not cached.







 

## Further Reading 

[live-element framework](https://live-element.net)

[Web Components at MDN](https://developer.mozilla.org/en-US/docs/Web/Web_Components)

[Building Components at Google Developers](https://developers.google.com/web/fundamentals/web-components)


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
