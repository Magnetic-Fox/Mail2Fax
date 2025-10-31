# E-Mail to Fax Relay Utility for Procmail and MGetty-Fax

## Introduction

The goal of this project is to provide very simple utility script for Linux, which transform e-mail messages (images + text parts) to TIFF image files and put prepared files in the fax spooler of MGetty-Fax package.
Provided script (with additional set of great tools, like MGetty, installed) is nearly an all-in-one solution that can send received e-mails as faxes to the phone numbers specified in the configuration file.

## Dependencies

**DISLAIMER:** *This solution was prepared as an utility for Linux OS-es (especially Debian). I don't know if it's possible to run it properly on other systems, because it's possible that some packages are missing for other environments.*

In brief, You'll need these packages to use this script:

* `python3` (of course)
* `PIL` (Pillow package for Python)
* `libtiff` (for Pillow to work properly with TIFF files)
* `imagemagick` (to convert image files)
* `paps` (to convert text to PostScript)
* `ghostscript` (to convert PostScript to G3 TIFF files)
* `mgetty` (to work with hardware modems)
* `mgetty-fax` (to support faxing feature of modems especially)
* `exim` (or another MTA)
* `procmail` (or similar; for invoking Python script)
* `fetchmail` (optional; needed if You wish to sync with remote mail server)

## Important note before going any further

Settings for this relay are stored in the `relay_settings.ini` file, which is provided with sample values.
Although they are in Polish, the file construction is self-explanatory - take a look at the keys to get the general meaning of the values.
You have to change at least the phone numbers to the desired ones.

## How it works?

This Python script works as a simple relay which reads e-mail from standard input and then processes it.
This solution is intended to be invoked by Procmail every time selected message arrives for a local account (this will be discussed in the next section).
The principle of operation is quite obvious:

1. the message containing specific subject arrives (for local user designated to run this script)
2. `procmail` manages to forward this message to this relay script
3. the message is then read from the standard input (`procmail` forwards it that way)
4. received data gets unpacked from the message and processed
5. unpacked text is converted to G3 TIFF using `paps` and Ghostscript (`gs`)
6. unpacked images are converted to TIFFs (not G3 ones, as `faxspool` generally don't need it) using `convert` from ImageMagick package
7. all created TIFFs are passed to the `faxspool` to queue the fax job
8. `faxspool` (or rather `faxrunq` and `faxrunqd`) does the rest in time (depending on configuration)

As I've mentioned before, to convert text to G3 TIFFs, the script needs to use `paps` and `gs` utilities.
Converting images is done by `convert` utility from `imagemagick` package. It makes it really good.

Of course, `convert` from ImageMagick can also perform text-to-image conversion, but results created by `paps` and `gs` are much better for faxing (or I just couldn't find best parameters for `convert` to create perfect quality monochrome text ;-)).

## Additional in-message switches

This script can dynamically set some settings according to the e-mail text.
This allows sender to decide how to send a fax to You (normal/fine quality, pictures only, etc.).

Current version supports two triggers (which can be changed and/or turned off in the configuration file):

* `!DISCARD!` - discard main text part (also containing headers) from the message (useful while sending images only)
* `!STANDARD!` - send fax in the standard resolution (as opposed to the default "fine" resolution)

Both triggers can be used in one message in any place of it.

Example message text:
```
Hello pal!

I'm sending You some pictures from my vacations.
However this text is not needed, so let it lay only in Your mail server's inbox and not a fax. ;)

!DISCARD!

Also I'd like to send everything quickier to You:

!STANDARD!

Greetings,
Your friend
```

Or something very simple:
```
!DISCARD!
!STANDARD!
```

## Configuration

### Preparation

First of all, make sure You've satisfied all the dependencies and configured the script properly. It's quite easy to test it.

1. You may send a simple message to yourself using `mail -s "[FAX] Test subject"` command (assuming You've configured `[FAX] ` as Your message trigger) and send yourself a simple mail. If everything is configured properly, Your mail should be processed and queued to fax in a few seconds.
2. You may send yourself a simple message with any subject using `mail -s "Test subject"` command, go to the `mail` program, and then save received mail to the text file (for example `test.txt`) and pass it to the script (`cat test.txt | ./relay.py`). Please note that this will send Your mail to the default phone number or may even do nothing, according to the configuration. To avoid such a situation pass the text file this way: `cat test.txt | ./relay.py FAX`, where FAX is the name of Your phone number setting.
3. You can also run this relay directly and write something, but remember to finish written line with `Enter` and then press `Ctrl+D` to finish the input stream.
Prepared message (in chosen way) should now be spooled for faxing to the number specified in the configuration file and suddenly arrive on the fax machine (depending on configuration of `mgetty-fax`).

If anything goes wrong at this point, there is probably something missing in the system or configuration.
**Remember to configure dependencies!** MGetty, MGetty-Fax, Exim4, etc...

### Choosing local account to receive e-mails

To make everything work properly, You have to decide which local account on Your Linux system has to "do the thing". It'll be needed to use its mailbox and allow it to run this relay and use `faxspool` command to queue faxes.

### Choosing subject trigger (recommended)

You probably don't want to pass all the messages to the fax machine.
It can even be dangerous to do so, especially in conjunction with default configuration of `mgetty-fax` as this would probably cause a loop of resending faxes after any (un)successful fax operation!
It's very good to choose some kind of a "subject trigger", which will decide which messages should be passed to the relay script and to which fax number.
In my example it'll be simply `[FAX] ` at the beginning of the subject.

### Make Procmail process every message arriving

To make it all work, You need to make Procmail process every message that'll arrive for the chosen user account.
To achieve this, You'll need `.forward` file in the chosen account's home directory.
This file is really simple, because it just has to invoke Procmail, so its content should look like this:
```
|/usr/bin/procmail
```

### Configuring Procmail

Now the final step is to create a `.procmailrc` file in the home directory of chosen user account.
You'll need to provide simple conditions, which will control which messages have to be sent to the script and to which number.
As these might be sent to You as a plain text, quoted printable or Base64, You'll need three conditions for one number.
See example below for three fax numbers.

```
#FAX3
:0
* ^Subject:.*\[FAX3\]*
| $HOME/Python/relay.py FAX3

:0
* ^Subject:.*W0ZBWDNd*
| $HOME/Python/relay.py FAX3

:0
* ^Subject:.*?Q?=5BFAX3=5D*
| $HOME/Python/relay.py FAX3

# FAX2
:0
* ^Subject:.*\[FAX2\]*
| $HOME/Python/relay.py FAX2

:0
* ^Subject:.*W0ZBWDJd*
| $HOME/Python/relay.py FAX2

:0
* ^Subject:.*?Q?=5BFAX2=5D*
| $HOME/Python/relay.py FAX2

# FAX
:0
* ^Subject:.*\[FAX\]*
| $HOME/relay.py

:0
* ^Subject:.*W0ZBWF0*
| $HOME/relay.py

:0
* ^Subject:.*?Q?=5BFAX=5D*
| $HOME/relay.py
```

In such case, it is really important to provide subject triggers for fax numbers in reverse order.
So, for example, all conditions for FAX4 in the first place, then FAX3, FAX2 and then the last one - just FAX.
It needs to be in such order for Procmail to work properly.

Now, let's take a look at the `FAX` subject trigger configuration (for Your first number).
In here, the first condition is just `[FAX]` but in plain-text escaped in the Unix way (the same way as You can see `\n`, `\t`, etc.).
The second condition is just `[FAX]` but Base64-encoded (**but**, without `=` at the end, **which is very important!**).
The third condition is just `[FAX]` but in the Quoted-Printable.

### Configuring Fetchmail (optional)

If You want to use remote server for receiving e-mails, You can use Fetchmail for this task running as a daemon.
To achieve this, create configuration file `/etc/fetchmailrc` with content similar to this (for IMAP server):

```
set daemon 900
set no bouncemail

poll <your_mail_server_here> protocol imap:
	username "<your_username_here>" password "<your_password_here>" is "<your_local_account_name_here>" here
	keep
	idle
	ssl;
```

This config file will instruct Fetchmail to work as a daemon and securely poll the server every 15 minutes and try to get the newest messages as quick as possible using IMAP IDLE protocol, keeping them undeleted in the inbox, and deliver them to the specified local user.

Finally, You may also need to enable starting Fetchmail as a daemon by changing `/etc/default/fetchmail` file settings.

### Testing

Now, if everything was configured properly, You can just send yourself an e-mail containing `[FAX] ` at the beginning of the mail subject (or other string, You decided to choose).
You can do this locally or remotely (if You're using Fetchmail). When the message arrive it'll make all that "machinery" run the Python code, which will process the message and then - send it as a fax to the chosen phone number. :)

## Known problems

I've made much effort to provide working code, but it is possible that it still contain bugs I haven't noticed. However, I hope there aren't any.

### Fetchmail don't work very well with IMAP IDLE

While testing, I've found that Fetchmail sometimes don't get new messages immediately from the remote server.
As far as I know, it's due to the problems with Keep Alive packets sent too late throught the long time SSL connection, which can render socket errors and make Fetchmail wait for the next poll time (which can even hang completely).

You may want to lower following values using `sysctl` to make everything work better, but (unfortunately) it still doesn't solve the problem completely:
```
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 24
net.ipv4.tcp_keepalive_probes = 6
```

This partial solution was found somewhere on the SourceForge (if I remember correctly).
Unfortunately, it's best to use just polling the mail inbox periodically than using IMAP IDLE.
To do so, just remove `idle` keyword from the configuration file.

### Fetchmail can't connect to the server

As e-mail providers are switching more and more to OAuth2 lately, which Fetchmail unfortunately can't use directly, You have to use some kind of a proxy to reach them.
You should be very interested in this awesome solution: [Email OAuth 2.0 Proxy](https://github.com/simonrob/email-oauth2-proxy) by Simon Robinson.
It works perfectly in my configuration for quite a long time without any issues. I highly recommend this great solution!

## Disclaimer

As I have mentioned before, I've made much effort to provide here working code and solutions with hope they'll be useful and free from any bugs.
However I can't guarantee anything. The software and solutions here are provided "AS IS" and **I take no responsibility for anything. You're using them on Your own risk!**

## License

Free for personal use.
Please do not use these solutions commercially (as they are not so good tested to be intended to).
However, if You still like to anyway, please ask me before.

Bartłomiej "Magnetic-Fox" Węgrzyn,
July 24, 2024 - October 31, 2025
