

**Getting started**

> Read the assessment first, then plan the whole thing before writing any code:
> what stack, how to deal with the messy seed data, which AI feature to build and
> what to test. Tell me where you'd do it differently.



**Data model and the messy seed**

> Set up the models for users, hardware and rentals. Then put the raw seed in its
> own file untouched and write something that imports it and cleans it up. Fix the
> obvious stuff like the brand typo and the weird date format, but don't quietly
> change anything you're not sure about — flag it on the record instead, and print
> what you change so I can see it.



**The API**

> Build the backend endpoints: JWT login with no public sign-up (only an admin
> creates accounts, hash the passwords), hardware list/add/delete with server-side
> sorting and filtering, and the rent/return flow. Make the impossible states
> impossible — can't rent something unavailable, can't return what isn't out, you
> can only return your own device — and send a proper error, not a 500.



**The AI part**

> Build the two AI features, the inventory auditor and the semantic search. Both
> should call Claude when there's an API key but fall back to plain logic when
> there isn't, so the demo still works with no key. The auditor should read the
> notes and flag things like "available but damaged". Don't fake it in the fallback.



**Catching the data loss** (this became "The Correction" in the README)

> Hang on — the seed has 11 devices but only 10 ended up in the database. What
> happened to the missing one?

That's how the two records sharing id 4 turned up. Follow-up:

> Stop using the seed's id as the primary key, it isn't unique. Give every row its
> own id, keep the original one in a separate column, and log the clash. Add a test
> so both id-4 devices are always kept.


**Tests and frontend**

> Write tests for the important rules against a throwaway database: can't rent
> broken or in-use gear, the normal rent/return works, both duplicate-id records
> survive, and only admins can create users. Then build the frontend in Vue 3 +
> Vite: one dashboard with the search bar on top of a sortable, filterable table
> with rent/return, and a separate admin page. Show whether the real AI or the
> fallback answered each search.


**Security pass**

> Go back over the auth and fix the real security holes. It shouldn't run in
> production with the default secret key or admin password, login shouldn't give
> away which emails exist, and add some protection against password guessing.
> Cover it with tests.
