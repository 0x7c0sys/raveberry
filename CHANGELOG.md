# Changelog

## 0.6.7 - 2020-06-10

- Users can vote 10 times in 30 seconds instead of once every 5 seconds
- Unavailable options are greyed out in settings

## 0.6.6 - 2020-06-11

- Requesting archived musiq also toggles the upvote button
- If more than one backend is configured, only one online suggestion per service is displayed
- [watson](https://github.com/etianen/django-watson) is used to search the database for suggestions

## 0.6.5 - 2020-06-08

- Bump django to 2.2.13

## 0.6.4 - 2020-05-20

- Started keeping this changelog.
- Songs are now upvoted automatically after requesting.  
This required removing the placeholders as a special queue instance. Now, every request results in a persisted queue entry that is removed on error. The db-key of this queue entry is handed back to the client for upvoting.  
As a side effect, the new placeholders can be reordered, voted for and even removed. This required some refactoring, but now the request process is a little less convoluted.
- Decreased the number of votes required to kick a song to 2, as every song starts out with 1 now.
- `module-bluetooth-policy` is loaded on boot, which is needed by some devices.
- Added version information in the settings.
- Added option to upgrade raveberry in the settings.
