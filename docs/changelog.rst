Changelog
=========

* :release:`2.38.2 <14-02-2019>`
* :bug:`-` Plugin method failures are now wrapped in ``handling_exceptions``, properly reporting failures when they happen
* :bug:`-` Fixed support for Windows systems (thanks @eliadh)
* :bug:`96` Fixed json encode-escaping when serializing API parameters
* :release:`2.38.1 <22-11-2018>`
* :bug:`87` Add timeouts to all requests by default to avoid stalled requests taking forever
* :release:`2.38.0 <23-10-2018>`
* :feature:`-` Support resuming sessions with unstarted-only or failed-only test filters
* :release:`2.37.1 <10-10-2018>`
* :release:`2.37.0 <16-9-2018>`
* :feature:`-` Slash plugin can now optionally report test docstrings as metadata (thanks @yaelmi3!)
* :release:`2.36.1 <15-7-2018>`
* :feature:`77` backslash-python now honors Slash's blacklist for performing ``repr`` on traceback distilling, if available
* :release:`2.36.0 <7-5-2018>`
* :feature:`72` Avoid reporting session_start once a session already exists
* :release:`2.35.0 <3-5-2018>`
* :feature:`73` Report parameter labels if available
* :feature:`-` Small improvement to how interactive tests get reported
* :release:`2.34.0 <15-3-2018>`
* :feature:`70` Configuration filename for the bundled Slash plugin can now be controlled through a constructor argument
* :feature:`68` Support blacklisting warning categories from being reported to backslash
* :release:`2.33.1 <30-1-2018>`
* :bug:`63` Avoid accidental deprecation when examining exception attributes
* :release:`2.33.0 <2-1-2018>`
* :feature:`61` The Slash plugin now serializes variables based on its own logic, and not Slash's. This is more future-proof, as Slash is going to deprecate this information in the upcoming release
* :release:`2.32.0 <30-10-2017>`
* :feature:`60` Clean up UI URL generation, added ``Backslash.get_ui_url`` helper method
* :feature:`59` Support reporting interruption exceptions to Backslash
* :feature:`58` Support reporting timing metrics
* :feature:`57` Support reporting test status description
* :release:`2.31.2 <14-9-2017>`
* :bug:`54` Handle cases of detached head correctly when deducing local branch
* :release:`2.31.1 <11-9-2017>`
* :bug:`53` Use api session when constructing lazy queries
* :release:`2.31.0 <10-9-2017>`
* :feature:`52` Support reporting sessions with a specific TTL, marking them for future deletion on the server. This can be also specified in the command-line, by passing ``--session-ttl-days=X``
* :feature:`51` Report local and remote SCM branches if supported
* :release:`2.30.0 <8-8-2017>`
* :feature:`50` Added session_webapp_url property to the Slash plugin
* :release:`2.29.0 <6-8-2017>`
* :feature:`49` Add hook for intercepting keepalive thread exceptions
* :feature:`-` Move to PBR
* :bug:`31 major` Be more resilient to I/O errors when compressing tracebacks
* :feature:`39` Added ``webapp_url`` and ``rest_url`` to the official Slash plugin
* :feature:`37` Support reporting fatal exceptions
* :feature:`36` Added ``get_parent`` to test objects to retrieve the parent session
* :release:`2.28.0 <15-05-2017>`
* :feature:`-` Added Slash plugin option to propagate exceptions (useful for debugging)
* :feature:`23` Enable injecting metadata via environment variables
