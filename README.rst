Introduction
============

Following discussions during the Vancouver OpenStack summit about the
level of technical debt of patches in packages, the prototyped tools
were created to explore these ideas.

Each package has a score which is the sum of the scores from each
patch using the following rules:

* Not submitted upstream -> +200
* Abandoned upstream -> +150
* Not merged upstream -> +20
* Merged upstream -> +10
* Cherry-picked upstream -> +10
* Do not pass Jenkins -> +50
* Got a +2 -> -10
* Lowest vote is -2 -> +100
* Lowest vote is -1 -> +50
* Lowest vote is +1 -> -5
* Difference to upstream patchset is null -> 0
* Difference to upstream patchset is small -> +10
* Difference to upstream patchset is big -> +100

For not gerrit managed project (mainly outside of OpenStack), the tool
tries to follow upstream submission using cherry-pick comments so it's
less precise.

Actions
=======

Actions that can be taken to lower the scores:

* be sure to have the Change-Id or cherry picked comment present.
* make the patchsets pass Jenkins.
* make the patchsets merged.
* use the current patchset when the patchset evolved in the review.

How it works
============

``extract.sh`` does the following in sequence:

* extract files from the src.rpm using rpm2cpio
* for each patch lookup the ``Change-Id:`` or the ``cherry picked from
  commit`` string.
* if patch is cherry-picked or in review, extract the patch from the
  git of the project using the id.
* compute an interdiff between the patches from the package and from
  the git repo.
* use diffstat to store statistics about the interdiff.
* if the patch is in review, extract the json info from gerrit.

``score.py`` computes a score from the review json and the interdiff
stats and generate HTML output on stderr.

You can use ``run.sh`` to download packages and then process them
through ``extract.sh`` and ``score.py``.

How to contribute
=================

We are not using PR from github but the review system from Software
Factory at http://softwarefactory.enovance.com/. So feel free to
submit reviews.
