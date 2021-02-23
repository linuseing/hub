# HUB

This project is version 3.x of an on modularity focused smart home hub.<br>
Whereas rivaHUB (version 2.x) tried to tidy up the messy, not well-thought-out and hard to maintain code structure of
home-control (version 1.x), <br>
This third and hopefully last full rewrite will focus on simplicity on the end user side of things,
and a refined plugin API for third and first party plugins.
This version will just be called 'HUB' right now, to make it more easy to change the name in the event of a better name idea.

# User focused changes
## Combining modularity and simplicity
The freedom that modularity features like the component based entity system provide comes at a high cost for the end user, 
mainly in form of large or complicated configuration files for entities/devices.
To solve this problem this version of the HUB will include simplified templates for common entities and workflows.
There will also be reserved device types with fixed constrains for the most used appliances, to unify internal and external API's 
(eg. frontends and mobile clients).

#Dev Focused changes