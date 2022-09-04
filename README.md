# THIS REPOSITORY

This repository is release zip of [nginxinc/nginx-amplify-agent](https://github.com/nginxinc/nginx-amplify-agent) v1.7.0-5, circa 2020-11-28-ish.

On around June 7th 2022, nginxinc deleted the old nginx-amplify-agent repository and replaced it with a new one - deleting the git history of the repo in the process and deleting any reference to the `packages/install-source.sh` script that I used as part of [Makeshift/docker-nginx-amplify](https://github.com/Makeshift/docker-nginx-amplify)'s CI process. (Admittedly I likely could have rewritten it in the time it took me to find, but I was sad to find the repository deleted, so I wanted a backup of it anyway. My data-hoarder instincts were apparently not strong enough to know that Nginx would delete a whole repository!)

I didn't have a copy of that script handy and couldn't find it online, so I used a [very old release](https://web.archive.org/web/20201128181127if_/https://codeload.github.com/nginxinc/nginx-amplify-agent/tar.gz/v1.7.0-5) that happened to be on archive.org.

Unfortunately, I was unable to find a copy of the git history to go along with this repo, but if any of the scripts in that repo were useful to anyone, here they are, hopefully as up to date as needed.

If anybody happens to come across this and has a copy of a later version of the code or a full copy of the repository, please do open an issue so I can update this copy.

# NGINX Amplify Agent

The NGINX Amplify Agent is a Python application that provides system and NGINX metric collection. It is part of NGINX Amplify — a free configuration monitoring tool for NGINX.

Please check the list of the supported operating systems [here](https://github.com/nginxinc/nginx-amplify-doc/blob/master/amplify-faq.md#21-what-operating-systems-are-supported).

This repository is not for installation purposes. To install the agent, please follow [this](https://github.com/nginxinc/nginx-amplify-doc/blob/master/amplify-guide.md#installing-and-managing-nginx-amplify-agent) document.

For more information about NGINX Amplify, please check the official documentation [here](https://github.com/nginxinc/nginx-amplify-doc).
