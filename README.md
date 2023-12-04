# python
A small library for handling mundane things.

When I worked at Google, one of the things that I liked was that every application, no matter what language it was written in, acted the same way.  C++, Python, Java, even Bash.  In particular, I liked:
* Flags defined at the module level
* Every log file in the same directory with the same naming format and content formatting

One other cool thing was that every single application automatically came with a web server that exported many common stats (well, not in Bash).  After all, some command line tools would still take several minutes to run (moving data across the network, for instance).

Much of the basics have been open sourced via the [Abseil](https://github.com/abseil) project.

However, when I first started writing Python projects for home, I wanted something similar, and the initial file, [app.py](https://github.com/nexushoratio/python/commit/ccb8792a059081e58b8af8f177466f3ada9d2d4d) was born.  (At the time, Google's Python version used that same name.)

Projects like [Click](https://palletsprojects.com/p/click/) did not exist yet, and [argparse](https://docs.python.org/3/library/argparse.html) was still the new hotness, so that became the basis (rather than something like getopt).

One problem with the Google flags system was they shared a global name space, across all of the languages.  A Python program that linked in C++ could use the C++ flags.  So it was not uncommon to discover that some flags added months or years ago suddenly conflict because of some new dependency.  I wanted to avoid that problem.  Plus, my skill with Python at the time was probably not up to getting it done quickly so I could actually use it.  And it stayed pretty stable for a while.  Then, for $REASONS, I stopped writing personal project and it stagnated, missing the whole Python 3 migration thing.

After finding an archive of the old git repository that had this, and other code in it, I attacked it with [git-filter-repo](https://github.com/newren/git-filter-repo) and uploaded it to my [Ingress](https://github.com/nexushoratio/ingress) repo as an example of work I'd done in the past.  Which lead me to getting back into that game, which has lead me to wanting to upgrade the code and make it usable again.

Recently, more *filter-repo* work has lead to this repo, for code that I originally shared between a variety of personal projects.  If nothing else, this will help expose me to how Python is done outside of Google's silo.  Lots to learn!
