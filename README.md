# nixpkgs-updaters-library

[![Support Ukraine](https://badgen.net/badge/support/UKRAINE/?color=0057B8&labelColor=FFD700)](https://www.gov.uk/government/news/ukraine-what-you-can-do-to-help)
[![Tests Status](https://github.com/PerchunPak/nixpkgs-updaters-library/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/PerchunPak/nixpkgs-updaters-library/actions?query=workflow%3Atest)

A boilerplate-less updater library for Nixpkgs bulk updaters.

The goal of this library is for you to write a simple script, that implements
a few abstract methods and classes, and get a powerful bulk updater in the
result.

> [!IMPORTANT]
> All code in this library was written by a human.

## Why?

Some types of packages are very simple to package. For example, Vim plugins
usually only require downloading a Git repository.

Now imagine having a thousand such plugins. Writing a separate package for each
one and keeping them all up to date would be a tedious task.

This library allows you to easily manage an unlimited number of packages.
Before it existed, many people would write a custom Python script and implement
all the required logic from scratch. Over time, as new features were added,
these scripts would grow in complexity and eventually become difficult to
maintain.

By using this library, we can avoid a lot of boilerplate code and gain many
powerful features out of the box. For example, it supports updating a single
plugin when you want to update only one package instead of all of them.

## Usage

Please consult our [documentation](https://nupd.perchun.it) for that.
