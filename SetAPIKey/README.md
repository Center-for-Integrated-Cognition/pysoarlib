# Setting OpenAI API Keys in Windows

Now that we have different OpenAI API keys for each person
per project, we need an easy way to switch them when
we switch projects.
This must work without putting any keys in the code
or anywhere in GitHub.
The actual keys must be kept very private just
on the given user's machine.

This README and other related files are all stored
in the `SetAPIKey` folder at the top level of
the pysoarlib repo.
The files there are set up to work on Peter's
Windows machine.
You will need to make a local copy for your machine
and do some editing.

**BEFORE EDITING ANY OF THESE FILES TO SET UP FOR
YOUR MACHINE, MAKE A LOCAL COPY OF THIS FOLDER
AND DO ALL YOUR EDITS THERE.**

This document explains one way of setting up these keys
for Windows.
Based on what is given here, similar techniques
should be possible for Mac or Linux OS's.
It works well for Peter, hopefully others can use it too.

## Get Your Keys from OpenAI

First log in to the OpenAI API web site using your CIC email.
Create a new account if needed.
This should get you connected to the CIC account, but
if it does not check with Bob or James on how to do that.

Once you're logged in, you should see `CIC` in the upper left
corner of the page, followed by a project name.
Open the dropdown list of projects and select the project
you want to work on.
Then go to the API Keys page.

If you already have a key for that project, it will appear.
If not, you should see a large button inviting you to create
a personal key for that project.
Click on that button, and a box with a long string for
the key should pop up.
Click the copy button.

## Save the Keys Privately

Save that string carefully in a text file that is in
some private place on your computer.

**NEVER SAVE ONE OF THESE KEYS IN A FILE THAT IS
ON GITHUB OR ONEDRIVE OR ANY OTHER CLOUD FOLDER.**

## Set Up Environment Variables

The next step is to set up enviroment variables on your
system for various different keys, according to your projects.
To get to these variables, right click on the Windows start
button and select System.
In the `Find a setting` box type `env` and then select
`Edit the system enviroment variables`.
A `System Properties` window will open.
Click on the `Environment Variables` button.
An `Environment Variables` dialog box will open with
two lists of variables, one for you as a user and
one for System variables.

On my machine, I prefer using the `System variables`.
I have created the following variables:

- `OPENAI_API_KEY`  This is the main key variable that
the code uses to access the API at run time.
It must be set correctly for the project you are
working on at the moment in order for the project
to be charged correctly.
- `OPENAI_DEFAULT_KEY` On my system this has the original
key I got when I first started using OpenAI years ago.
This key is attached to the `Default project` for CIC
on the OpenAI site.
This is not needed. If you don't have a default key,
forget it.
- `OPENAI_CASC2_KEY` This is my key for the CASC2 project.
- `OPENAI_THOR_SOAR_KEY` This is my key for the Thor-Soar project.

**NOTE:** Never use dash characters in these variable names, 
they will not work. Use underscore instead.

To summarize, the `OPENAI_API_KEY` variable is dynamic.
Its value will change when you switch projects,
since this is the key used to access the real API.
The others are person-project specific keys that are
stored in additional environment variables to make
it easy to switch projects.
Their values should never change.

## Set Up .ps1 Scripts

The `SetAPIKey` folder in the pysoarlib repo has two `.ps1` files, which
are scripts to run in Windows PowerShell.
Each one has a command to set the main
`OPENAI_API_KEY` variable to my personal key for a particular project.
`GoCASC2.ps1` will set me up for the CASC2 project,
and `GoThorSoar.ps1` sets my up for Thor-Soar.

You may need to edit these files in your local copy of the `SetAPIKey` folder.
My `GoThorSoar.ps1` file sets the key to my Thor-Soar key with this command:

```
[Environment]::SetEnvironmentVariable('OPENAI_API_KEY',$Env:OPENAI_THOR_SOAR_KEY,'Machine')
```

For each project you work on, you will need a `.ps1` file looking like this,
except that you will have to change the name of the project-specific key
to the name you are using for that variable.
The function of that command is to set the value of the `OPENAI_API_KEY`
variable to a copy of the value of the other variable named.
If you prefer to use user variables instead of system variables,
change the third argument from `Machine` to `User`.

These `.ps1` scripts have to be run in Administrator mode.
With no further work, that is not easy to do. You have to
open a PowerShell in Adminstrator mode, go to the correct folder,
and then type the command to run the script.

## Set Up Shorcuts

To make that easy, we need a shortcut for each project.
Setting these up is a bit complicated.
The `LaunchElevatedPowerShell.pdf` file has instructions
obtained online for doing this.
That file describes three possible methods.
These instructions are based on Method 2.

The `GoCASC2` and `GoThorSoar` shortcuts provided in the `SetAPIKey`
folder work on my machine.
Rather than going through all of Method 2, these can be edited as follows.

1. Right click on one of these shortcuts and select `Properties`.
2. Edit the `Target` field so that the path at the end points to
the `.ps1` script you want this shortcut to run.

You can set up for other projects by simply copying one of these
shortcuts, renaming it, and pointing it to a `.ps1` file set
up for the desired project.

## Enjoy!

With all this done, just copy these shortcut
files onto your desktop.
When you double click one of them, a window comes up
asking if you want to give this app permission to
modify your system.
Say `Yes` and the script will magically set the
main `OPENAI_API_KEY` environment variable to point to
your personal key value for the given project.
Voila!

You can check that the `OPENAI_API_KEY` was changed
properly in one of two ways:
1. By using the `Environment Variables` dialog
described above.
2. By opening a PowerShell window as administrator.
Right click on the Windows Start icon and select `Terminal (Admin)`.
The following command will show you the current value of
the `OPENAI_API_KEY` when PowerShell was opened:

```
 $Env:OPENAI_API_KEY
```

Remember that when you open either the `Environment Variables` dialog
or a PowerShell window, that window captures
the current value of the variables when it was opened.
If you change a variable using one of your shortcuts
and want to confirm the change was made,
you have to reload the `OPENAI_API_KEY` variable.
1. For the `Environment Variables` dialog,
close that dialog and reopen it to see the changed value.
2. For a Powershell Window execute this command:
```
$Env:OPENAI_API_KEY = [System.Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Machine")
```
and then use the previous command to print
the `OPENAI_API_KEY` variable again.

**NOW ENJOY USING THE OpenAI API WITH A KEY SET TO CHARGE
YOUR PROJECT CORRECTLY BY SIMPLY RUNNING THE SHORTCUT
YOU SET UP FOR THAT PROJECT BEFORE STARTING YOUR WORK.**

