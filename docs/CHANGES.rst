Changelog
=========

1.7.8 (unreleased)
------------------

- TBD


1.7.7 (2015-08-11)
------------------

- Fix: when the last applied upgrade step had a checker, the profile
  version was not updated.  Now we no longer look at the checker of
  the last applied step when deciding whether to set the profile
  version.  The checker, if any is set, normally returns True before
  running the step (it can be applied), and False afterwards (it
  was already applied).

- Add ``upgradeProfile`` method to setup tool.  This method applies all
  upgrades steps for the given profile, or updates it to the optional
  given version.  If the profile does not exist, or if there is no upgrade
  step to go to the specified version, the method warns and does nothing.

- Check the boolean value of the ``remove`` option when importing
  objects.  Previously we only checked if the ``remove`` option was
  given, regardless of its value.  Supported are ``True``, ``Yes``,
  and ``1``, where case does not matter.  The syntax for removing
  objects, properties, and elements is now the same.

- Support ``remove="True"`` for properties.


1.7.6 (2015-07-15)
------------------

- Enable testing under Travis.

- Fix compatibility with Setuptools 8.0 and later.  Upgrade steps
  could get sorted in the wrong order, especially an empty version
  string (upgrade step from any source version) sorted last instead of
  first.


1.7.5 (2014-10-23)
------------------

- Allow skipping certain steps on ``runAllImportStepsFromProfile``.


1.7.4 (2013-06-12)
------------------

- On import, avoid clearing indexes whose state is unchanged.


1.7.3 (2012-10-16)
------------------

- Sort profiles on Upgrade form.

- Use clickable labels with checkboxes on import, export and upgrade forms
  to improve usability.


1.7.2 (2012-07-23)
------------------

- Avoid using ``manage_FTPGet`` on snapshot exports: that method messes
  up the response headers.

- ZopePageTemplate handler:  Fix export encoding: since 1.7.0, exports
  must be UTF-8 strings


1.7.1 (2012-02-28)
------------------

- Restore the ability to make the setup tool use only import / export
  steps explicitly called out by the current profile, ignoring any which
  might be globally registered.  This is particularly useful for configuring
  sites with baseline profiles, where arbitrary add-on steps are not only
  useless, but potentially damaging.


1.7.0 (2012-01-27)
------------------

- While importing ``toolset.xml``, print a warning when the class of a
  required tool is not found and continue with the next tool.  The
  previous behaviour could break the install or uninstall of any
  add-on, as the missing class may easily be from a different
  unrelated add-on that is no longer available in the zope instance.

- Exporters now explicitly only understand strings. The provided
  registry handlers encode and decode data automatically to and from
  UTF-8. Their default encoding changed from None to UTF-8.
  If you have custom registry handlers, ensure that you encode your unicode.
  Check especially if you use a page template to generate xml. They return
  unicode and their output must also encoded.
  If you choose to encode your strings with UTF-8, you can be sure that
  your code will also work with GenericSetup < 1.7
