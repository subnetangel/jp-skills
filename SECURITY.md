# Security policy

## What is in scope

This repository holds agent skills: markdown instructions, Python and Node scripts that run on your own machine, and
HTML templates that open from local files. Nothing here runs a server or calls a network service. Reports that
matter most:

- A script that writes outside the folder it was given, runs something it should not, or leaks file contents.
- A template or build that fetches from the network when it claims to be offline, or that keeps something in a
  share build that should have been removed (speaker notes, the staff code hash).
- A skill instruction that would lead an agent to expose secrets, identifiers or private data.

The demo-engine staff code is a convenience gate for a booth, not security; a way to read the page's content is
not a vulnerability. A way to recover the code from something other than its hash would be.

## How to report

Please report privately, not in a public issue.

TODO (maintainer): add a private contact method, for example GitHub's "Report a vulnerability" (private
vulnerability reporting) on this repository, before it is made public.

Include what you ran, what happened, and what you expected. You should get an acknowledgement within a week.

## Supported versions

Only the latest commit on `main` is supported.
