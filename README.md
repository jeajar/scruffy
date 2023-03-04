
<p align="center">
  <img src="./email_templates/scruffy.png">
</p>

# Scruffy, the Janitor
Scruffy, the janitor is responsible to delete media requested by users.
For when your friends and family members are out of control with requests.

**Note** Current project status: Proof of concept

## The Problem
Overseerr is an amazing request application but the project has decided, at least for the time being, that it is not responsible for deleting media even if it has API access to Plex, Radarr and Sonarr. We need a process to handle this externally.

## Proposal
* Scruffy should work with individual movies and tv series. We will call this a **media entity**.
* Scuffy should automatically delete a **media entity** with a *n* days warning if the following criteria are met:
    * The **media entity** was requested via Overseer.
    * The user who requested the **media entity** has watched it.
    * All users who added the **media entity** to their watchlist have also watched it.
* Scruffy should send a grouped notification with all **media entities**. We will refer to this as a **delete job**.
* Scans to send a **delete job** should be configurable like a cron job.
* The sceduled time when a **delete job** is run should also be configurable. Ex. delete in 7 days at 03:00
* A user should be able to add or remove a **media entity** to his or her watchlist at any time and alter which **media entity(ies)** are included in the **delete job**

## MVP (Miminum viable product)
* The logic should be implemented and scruffy should be able to correctly delete **media entities** notifications, warning and scedule delete will come later.

## Technical
* Use yaml for configuration
* No WebUI, we have enough fucking UIs with all the *arr
* CLI application only
* sqlite datase enough?
* Don't forget, this should be a feature in Overseer, this code should not exists so, KISS :D