# Very Simple E-Mail to Fax Relay Utility for Procmail

## Introduction

The goal of this project is to provide very simple utility script for Linux, which transform e-mail messages (images + text parts) to TIFF image files (used to fax transmission). Provided script is nearly an all-in-one solution that can send fax after receiving an e-mail on the standard input.

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

**Settings for this relay are now stored in the `relay_settings.ini` file**, which is provided with sample values here. They are in Polish, but somehow self-explanatory (take a look at the keys to get meaning of the values).
You have to change at least the phone number to desired one.
Please also note that the **default message trigger has been changed to just `!DISCARD!`** which is much easier to remember and looks far better than its previous version (`?????NOTEXT?????`).

## How it works?

This Python script works as a simple relay invoked by Procmail every time desired message arrives for a local account (this will be discussed in the next section).
The principle of operation is quite obvious:

1. the message is read from standard input
2. received data gets unpacked and processed
3. unpacked text is converted to G3 TIFF
4. unpacked images are also converted to TIFFs
5. all created TIFFs are passed to the `faxspool` to queue the fax job

To convert text to G3 TIFFs, the script needs to use `paps` and `ghostscript` utilities. Yeah, I know `imagemagick` can do the same, but results created by `paps` are just much better and using this tool is also a bit easier. Of course, it is also necessary to convert the actual result from `paps` using `ghostscript`.

Converting images can be done by `convert` utility from `imagemagick` package. It makes it really good.

## Configuration

### Preparation

First of all, make sure You've satisfied all the dependencies and configured the script properly. It's quite easy to test it. You may send a simple message to yourself using `mail -s "Test subject"` command, then save it to a `test.txt` text file and pass it to the script.

For example, `cat test.txt | ./relay.py`, will make the script process the message contained in the `test.txt` file and send it to the phone number specified in constants.

**Of course, I assume, You've configured `mgetty-fax` and `exim` packages before.**

### Choosing local account to receive e-mails

Decide which local account on Your Linux system has to "do the thing". It'll be needed to use its mailbox.

### Choosing subject trigger (optional, but recommended)

You probably don't want to pass all the messages to the fax machine. It's good to choose some kind of a "subject trigger", which will decide which messages should be passed to the relay script. In my example it'll be simply `[FAX]` at the beginning of the subject.

### Make Procmail process every message arriving

To make Procmail process every message that'll arrive, You'll need `.forward` file in the chosen account's home directory.
This file just has to invoke Procmail, so its content might be as simple as this:
```
|/usr/bin/procmail
```

### Configuring Procmail

Create the `.procmailrc` file in home directory of chosen account. You'll need to provide simple conditions, which will control which messages have to be sent to the script. As these might be sent to You as a plain text, quoted printable or Base64, You'll need at least these three conditions:

```
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

The second condition is just `[FAX]` but Base64-encoded (without `=` at the end, which is very important!).

### Configuring Fetchmail (optional)

If You like to use remote server to receive e-mails, You can use Fetchmail running as a daemon.
To achieve this, create configuration file `/etc/fetchmailrc` with content like that (for IMAP server):

```
set daemon 600
set no bouncemail

poll <your_mail_server_here> protocol imap:
	username "<your_username_here>" password "<your_password_here>" is "<your_local_account_name_here>" here
	keep
	idle
	ssl;
```

This config file will instruct Fetchmail to work as a daemon and securely poll the server every 10 minutes and try to get the newest messages as quick as possible using IMAP IDLE protocol, keeping them undeleted in the inbox, and deliver them to the specified local user.

Finally, You may also need to enable starting Fetchmail as a daemon by changing `/etc/default/fetchmail` file settings.

### Testing

Now, if everything was configured properly, You can just send yourself an e-mail containing `[FAX]` at the beginning of the mail subject (or other string, You decided to choose). You can do it locally or remotely (if You're using Fetchmail). When the message will arrive it'll make all that "machinery" run the Python code, which will process the message and then - send it as a fax to the chosen phone number. :)

## Known problems

I've made much effort to provide here working code, but it is possible that it still contain bugs. However, I couldn't find any for now.

### Fetchmail don't work very well with IMAP IDLE

While testing, I've found that Fetchmail sometimes don't get new messages immediately from the remote server. As far as I know, it's due to the problems with Keep Alive packets and SSL support, which can render socket errors and make Fetchmail wait for the next poll time.
You may want to lower these values using `sysctl` to make everything work better, but (unfortunately) it still doesn't solve the problem completely:

```
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 24
net.ipv4.tcp_keepalive_probes = 6
```

This partial solution was found somewhere on the SourceForge (if I remember correctly).

## Disclaimer

As I have mentioned before, I've made much effort to provide here working code and solutions with hope they'll be useful and free from any bugs. However I can't guarantee anything. The software and solutions here are provided "AS IS" and **I take no responsibility for anything. You're using them on Your own risk!**

## License

Free for personal use. Please do not use these solutions commercially (as they are not so good tested to be intended to). However, if You still like to anyway, please ask me before.

Bartłomiej "Magnetic-Fox" Węgrzyn,
24th July 2024 - 5th April 2025.