
<p align="center">
  <img src="./email_templates/scruffy.png">
</p>

# Scruffy, the Janitor
Scruffy, the janitor is responsible to delete media requested by users with Overseerr.
For when your friends and family members are out of control.

**Note** Current project status: Proof of concept

## The Problem
Overseerr is an amazing request application but the project has decided, at least for the time being, that it is not responsible for deleting media even if it has API access to Plex, Radarr and Sonarr. We need a process to handle this externally.

## Proposed Features:
* Scruffy handles media requests like a library loan. Media on disk is deleted X days after they have been added (made available).
* Scruffy don't punish the user if stuff takes time to download. The loan period starts when all the requested media is available.
* A Request is either a Movie or a TV Request for any number of seasons. If a users asks for 97000 seasons of a 
show, they will have 30 days to watch all of it. 
* Scruffy doesn't care about watch data. You request it, you don't watch it? Too bad, it's gone after 30 days.
* Scruffy is at least going to notify you by email a week before stuff gets deleted.
* The user should be able to click a link to ask for an extension, at least once.
* Scuffy should remain simple and run as a cron or sceduled job, no fancy UI.
