# E-Mail to Fax Relay Utility for Procmail and MGetty-Fax

## Introduction

The goal of this project is to provide very simple utility script for Linux, which transform e-mail messages (images + text parts) to TIFF image files and put prepared files in the fax spooler of MGetty-Fax package.
Provided script is nearly an all-in-one solution that can send fax after receiving an e-mail on the standard input.

## Dependencies

**DISLAIMER:** *This solution was prepared as an utility for Linux OS-es (especially Debian). I don't know if it's possible to run it properly on other systems, because it's possible that some packages are missing for other environments.*

In brief, You'll need these packages to use this script:

* `imagemagick`
* `ghostscript`
* `paps`
* `mgetty`
* `mgetty-fax`
* `exim` (or another MTA)
* `procmail` (or similar; for invoking Python script)
* `fetchmail` (if You want to sync with remote mail server)

Depending on how would You like to use this solution, You may need `fetchmail` or not.

## Important note before going any further

Settings for this relay are stored in the `relay_settings.ini` file, which is provided with sample values here.
Although they are in Polish, the file construction is self-explanatory - take a look at the keys to get meaning of the values.
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
8. `faxspool` does the rest in time (depending on configuration)

As I've mentioned before, to convert text to G3 TIFFs, the script needs to use `paps` and `gs` utilities.
Yeah, I know `convert` from ImageMagick can also do this, but results created by `paps` are much better for faxing.
Converting images is done by `convert` utility from `imagemagick` package. It makes it really good.

## Additional in-message switches

This script can dynamically set some settings according to the e-mail text.
Current version supports two triggers (which can be changed and/or turned off in the configuration file):

* `!DISCARD!` - discard main text part (also containing headers) from the message (useful while sending images only)
* `!STANDARD!` - send fax in the standard resolution (as opposed to the default "fine" resolution)

Both triggers can be used in one message in any place of it.

Example message text:
```
Hello pal!

Sending You some pictures from my vacations.
However this text is not needed. ;)

!DISCARD!

Also I'd like to send them quickier to You:

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

First of all, make sure You've satisfied all the dependencies and configured the script properly.
It's quite easy to test it. You may send a simple message to yourself using `mail -s "Test subject"` command, then save it to a `test.txt` text file and pass it to the script (`cat test.txt | ./relay.py`).
You can even run this relay directly and write something, but remember to finish written line with `Enter` and then to press `Ctrl+D` to finish the input stream.
Prepared message (in chosen way) should now be spooled for faxing to the default number specified in the configuration file and suddenly arrive on the fax machine (depending on configuration of `mgetty-fax`).
If anything goes wrong at this point, there is probably something missing in the system or configuration.

**Of course, I assume, You've configured `mgetty-fax` and `exim` packages before.**

### Choosing local account to receive e-mails

Decide which local account on Your Linux system has to "do the thing". It'll be needed to use its mailbox.

### Choosing subject trigger (optional, but recommended)

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
You'll need to provide simple conditions, which will control which messages have to be sent to the script and for which number.
As these might be sent to You as a plain text, quoted printable or Base64, You'll need three conditions for one number.
See example below for two fax numbers.

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

In such case, it is really important to provide subject triggers for fax numbers in reverse order, so (for example) all conditions for FAX4 in the first place, then FAX3, FAX2 and then the last one - just FAX.
It needs to be in such order for Procmail to work properly.

Now, let's take a look at the `FAX` subject trigger configuration (for Your first number).
In here, the first condition is just `[FAX]` but in plain-text escaped in the Unix way (the same way as You can see `\n`, `\t`, etc.).
The second condition is just `[FAX]` but Base64-encoded (**but**, without `=` at the end, **which is very important!**).
The third condition is just `[FAX]` but in the Quoted-Printable. Yes, there are still messages arriving in such coding, so it is important to have this condition.

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

This config file will instruct Fetchmail to work as a daemon and securely poll the server every 15 minutes and try to get the newest messages as quick as possible using IMAP IDLE protocol,
keeping them undeleted in the inbox, and deliver them to the specified local user.

Finally, You may also need to enable starting Fetchmail as a daemon by changing `/etc/default/fetchmail` file settings.

### Testing

Now, if everything was configured properly, You can just send yourself an e-mail containing `[FAX] ` at the beginning of the mail subject (or other string, You decided to choose).
You can do this locally or remotely (if You're using Fetchmail). When the message arrive it'll make all that "machinery" run the Python code, which will process the message and then - send it as a fax to the chosen phone number. :)

## Known problems

I've made much effort to provide working code, but it is possible that it still contain bugs I haven't noticed. However, I hope there aren't any.

### Fetchmail don't work very well with IMAP IDLE

While testing, I've found that Fetchmail sometimes don't get new messages immediately from the remote server.
As far as I know, it's due to the problems with Keep Alive packets and SSL support, which can render socket errors and make Fetchmail wait for the next poll time.
You may want to lower these values using `sysctl` to make everything work better, but (unfortunately) it still doesn't solve the problem completely:

```
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 24
net.ipv4.tcp_keepalive_probes = 6
```

This partial solution was found somewhere on the SourceForge (if I remember correctly).
Unfortunately, it's best to use just polling the mail inbox periodically than using IMAP IDLE.
To do so, just remove `idle` keyword from the configuration file.

## Disclaimer

As I have mentioned before, I've made much effort to provide here working code and solutions with hope they'll be useful and free from any bugs.
However I can't guarantee anything. The software and solutions here are provided "AS IS" and **I take no responsibility for anything. You're using them on Your own risk!**

## License

Free for personal use.
Please do not use these solutions commercially (as they are not so good tested to be intended to).
However, if You still like to anyway, please ask me before.

Bartłomiej "Magnetic-Fox" Węgrzyn,
24th July 2024 - 27th August 2025.