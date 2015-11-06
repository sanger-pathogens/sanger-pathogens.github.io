# Config

This directory should include one file per repo called `<REPO_NAME>.yml`.
These files should include keys and values which will be used to complete
or override the data collected from Github.com.

The most common use for this directory is probably to give specific scores to
promote or demote them in the rankings.

For example:

```
# Test repo.yml
---
title: "Ben's awesome project"
description: An example project for exampling things
readme: |
  This repo is pretty
  great.

  This is a new paragraph
score: 1000
```

or

```
# json2email.yml
---
score: -10
```
