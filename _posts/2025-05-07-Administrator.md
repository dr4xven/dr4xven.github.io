---
icon: fas fa-info-circle
order: 4
categories: HackTheBox
tags: ACL PSAFE3 DNCSync FTP Spraying Keberoasting GenericWrite GerenericAll backup.psafe3 WinRM
image: https://pbs.twimg.com/media/Gb3oaZMWAAA4z0N.jpg
---

## 🏮 Introduction
Hello I'm Dr4xven and welcome back to the my series of Active Directory Machines Exploitation

Lets get our hhands dirt by compromising this Lab `Administrator`, it is a medium-difficulty Windows machine on Hack The Box that simulates a full Active Directory domain compromise. It challenges the attacker to chain together multiple stages of enumeration, privilege escalation, and credential abuse — reflecting real-world attack paths commonly exploited in enterprise environments.

The engagement begins with access to a low-privileged user, and through meticulous analysis of Access Control Lists (`ACLs`), we discover that the user olivia has `GenericAll rights` over the account michael, enabling us to reset his password. Once we gain access as michael, further enumeration reveals his ability to reset the password of benjamin, which leads to access over `FTP`. There, we discover and crack a `backup.psafe3` file, revealing a trove of user credentials.

Credential `spraying` against the domain identifies valid access for the user emily, who holds `GenericWrite` permissions over the user ethan. We leverage this to perform a targeted `Kerberoasting` attack, successfully cracking ethan's credentials. With these, we confirm that ethan possesses `DCSync` privileges — ultimately allowing us to extract the Administrator hash and achieve full domain compromise.

This lab is an excellent exercise in understanding privilege escalation paths, abuse of Active Directory misconfigurations, and post-exploitation tactics in domain environments.

## 🧐 Enumeration
The initial phase of this engagement focuses on identifying accessible services and collecting information about the domain environment to map out possible attack vectors. With credentials for a low-privileged user provided, we begin by performing both network-level and domain-level reconnaissance.

### Credentials
```
Username: olivia
Password: ichliebedich
```
Ports and services enumeration

```php
nmap -sS -sC -sV 10.10.11.42
```

Results
```
Nmap scan report for administrator.htb (10.10.11.42)

Host is up (0.072s latency).

Not shown: 988 closed tcp ports (reset)

PORT     STATE SERVICE       VERSION

21/tcp   open  ftp           Microsoft ftpd

| ftp-syst: 

|_  SYST: Windows_NT

53/tcp   open  domain        Simple DNS Plus

88/tcp   open  kerberos-sec  Microsoft Windows Kerberos (server time: 2024-12-05 14:37:40Z)

135/tcp  open  msrpc         Microsoft Windows RPC

139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn

389/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: administrator.htb0., Site: Default-First-Site-Name)

445/tcp  open  microsoft-ds?

464/tcp  open  kpasswd5?

593/tcp  open  ncacn_http    Microsoft Windows RPC over HTTP 1.0

636/tcp  open  tcpwrapped

3268/tcp open  ldap          Microsoft Windows Active Directory LDAP (Domain: administrator.htb0., Site: Default-First-Site-Name)

3269/tcp open  tcpwrapped

Service Info: Host: DC; OS: Windows; CPE: cpe:/o:microsoft:windows

 

Host script results:

| smb2-security-mode: 

|   3:1:1: 

|_    Message signing enabled and required

|_clock-skew: 6h46m00s

| smb2-time: 

|   date: 2024-12-05T14:37:51

|_  start_date: N/A
```

With these ports open I did some deep and focused enumeration 
```php
    21 FTP Microsoft ftpd

    53 DNS Simple DNS plus

    88 Kerberos Kerberos

    135 RPC RPC

    139 NETBIOS NETBIOS

    389 LDAP LDAP

    445 SMB SMB
```

📁 SMB Enumeration: From Null Sessions to Credentialed Access

To assess the accessible shares and services, I began with SMB enumeration. Using crackmapexec, I tested both anonymous (null) access and authenticated access with the provided credentials.

```php
crackmapexec smb 10.10.11.130
```
![screenshot](assets/screenshots/Administrator/1.png)
While null sessions were not permitted, credentialed access revealed that the user olivia had login capabilities via WinRM (Windows Remote Management) — a key finding that confirmed remote code execution was possible. 

To establish an initial foothold on the target system, I leveraged the `evil-winrm tool`, which enabled secure remote access via the WinRM protocol.
```php
evil-winrm -i administrattor.htb -u 'Olivia' -p 'ichliebedich'
```
![screenshot](assets/screenshots/Administrator/2.png)

After successfully gaining access to the system, I proceeded to enumerate all local user accounts by executing the `net user` command.

![screenshot](assets/screenshots/Administrator/3.png)

With the list of local users obtained, the next step involved identifying remote login-capable accounts. This helps determine which users can authenticate over services such as `WinRM` for potential further access.

![screenshot](assets/screenshots/Administrator/4.png)

After identifying user accounts, I encountered a challenge—none of the credentials were valid for authentication. To address this, I conducted a registry inspection to uncover any potentially stored credentials. I used the following commands to search for plaintext passwords or saved credentials within the registry:

```php
reg query HKLM\SAM /f password /s
reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings /v ProxyUser
```
![screenshot](assets/screenshots/Administrator/5.png)

These commands aimed to locate weakly protected credentials often stored in commonly targeted registry locations.

Unfortunately, the registry search did not reveal any stored passwords. Although this was a potential avenue for credential discovery, it ultimately yielded no usable results. This highlights the importance of exploring multiple enumeration vectors during a domain compromise.

## 🔍 BloodHound Enumeration via bloodhound-python

To gather detailed information about the Active Directory (AD) environment and identify potential attack paths, I used the bloodhound-python tool. The following command was executed:

```php
bloodhound-python -v -u Olivia -p ichliebedich -ns 10.10.11.42 -d administrator.htb --dns-tcp -c All
```

Breakdown of the command:

    -v: Enables verbose output, providing real-time feedback as data is collected.

    -u Olivia: Specifies the username Olivia for authentication.

    -p ichliebedich: Provides the corresponding password for the user.

    -ns 10.10.11.42: Sets the nameserver to the target domain controller's IP address (10.10.11.42).

    -d administrator.htb: Defines the domain to enumerate, in this case, administrator.htb.

    --dns-tcp: Forces DNS queries to use TCP instead of UDP (more reliable for larger queries).

    -c All: Collects all available data types supported by the tool (e.g., sessions, ACLs, group memberships, etc.).

This command allows to gather a full picture of the AD environment, including user permissions, group memberships, session information, and delegation rights. The collected data can later be visualized in the BloodHound GUI to identify privilege escalation paths and misconfigurations.
```php
bloodhound-python -v -u Olivia -p ichliebedich -ns 10.10.11.42 -d administrator.htb --dns-tcp -c All
```
![screenshot](assets/screenshots/Administrator/8.png)

### 🔎 BloodHound Analysis & Ownership Delegation

After successfully collecting the data using bloodhound-python, I uploaded it to the BloodHound-CE interface for analysis. To begin the investigation, I set the Olivia user as the starting point by marking her as the owned principal within BloodHound.

From there, I explored outbound object relationships—the users and assets over which Olivia has some level of control or privilege. This helped identify potential lateral movement or privilege escalation paths originating from the Olivia account.

![screenshot](assets/screenshots/Administrator/6.png)

## 🛠️ Privilege Escalation via GenericAll on Michael

Upon analyzing the outbound object relationships in BloodHound, it was identified that the user Olivia holds GenericAll privileges over the Michael user account. This level of access grants full control, including the ability to reset the target's password.

Leveraging this, I forcefully reset Michael’s password, effectively gaining unauthorized access to his account—enabling the next stage of lateral movement within the domain.

```php
net user michael Password123
```
![screenshot](assets/screenshots/Administrator/7.png)

## 🧩 Privilege Escalation via ForceChangePassword
Based on the BloodHound analysis, it was identified that Michael holds the ForceChangePassword privilege over the user Benjamin. Leveraging this insight, I performed a password reset on Benjamin’s account without requiring his current credentials — an effective technique when such delegated rights are misconfigured in an Active Directory environment.
```php
net rpc password "benjamin" "Batman@123" -U "administrator.htb"/"michael"%"Password123" -S "administrator.htb"
```
### 📁 Credential Validation and FTP Access

Using the valid credentials:

    administrator.htb\olivia : ichliebedich

    administrator.htb\michael : Password123

    administrator.htb\benjamin : Batman@123

I compiled user and password lists, then systematically tested them across available services. During this enumeration, FTP access was successfully obtained using Benjamin’s credentials, revealing a potential data exposure vector.

## 🧿 Accesssing the FTP
```php
ftp administrator.htb
```
![screenshot](assets/screenshots/Administrator/10.png)

While enumerating the accessible FTP service using Benjamin’s credentials, I discovered a file named `Backup.psafe3`. Recognizing the potential sensitivity of this file, I downloaded it to my local attacking machine for further analysis and potential credential extraction.
![screenshot](assets/screenshots/Administrator/11.png)

### 🔐 Cracking the Backup.psafe3 File

The Backup.psafe3 file appeared to be a KeePass database. I extracted its hash and performed a password cracking attack using Hashcat, which successfully revealed the master password. This granted access to the stored credentials within the database.
![screenshot](assets/screenshots/Administrator/12.png)

The Password was serverd here
![screenshot](assets/screenshots/Administrator/13.png)

With the cracked master password, I successfully unlocked the Backup.psafe3 file. Inside, I uncovered multiple stored credentials, which expanded my access within the domain and enabled further privilege escalation.
![screenshot](assets/screenshots/Administrator/14.png)

The Credentials
![screenshot](assets/screenshots/Administrator/15.png)

Using the retrieved credentials, I successfully authenticated as the user emily, gaining a new foothold in the environment for further enumeration and privilege escalation.

![screenshot](assets/screenshots/Administrator/16.png)

Upon enumerating the user emily’s desktop, I successfully located the user flag, marking a significant milestone in the exploitation process.
![screenshot](assets/screenshots/Administrator/17.png)

## 🔥 Targeted Keberosting
To escalate the attack further, I leveraged the targetedkerberoasting.py script from GitHub, using the credentials of user emily. This allowed me to perform a targeted Kerberoasting attack, aiming to retrieve service account hashes that could potentially lead to higher-privileged accounts.
![screenshot](assets/screenshots/Administrator/19.png)

After retrieving the Kerberos service ticket hash from the targeted Kerberoasting attack, I used John the Ripper to successfully crack it. The cracked credentials granted access to the user ethan, advancing us significantly toward full domain compromise.
```php
john admin_hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```
![screenshot](assets/screenshots/Administrator/20.png)

## 🔑 DCSync Attack for Privilege Escalation

With valid credentials for the user ethan, I attempted access via WinRM but was unsuccessful. Based on BloodHound analysis, I confirmed that ethan possessed DCSync privileges. Leveraging this, I executed a DCSync attack to extract secrets from the domain controller, ultimately retrieving the NTLM hash of the Administrator account, leading to full domain compromise.

```php
impacket-secretsdump "administrator.htb/ethan:limpbizkit"@"dc.administrator.htb"
```
![screenshot](assets/screenshots/Administrator/21.png)

## 🔐 Final Step: Administrator Access via WinRM

After successfully dumping the Administrator NTLM hash through the DCSync attack, I performed a pass-the-hash authentication using evil-winrm, gaining privileged access to the domain as Administrator.
```php
evil-winrm -i administrator.htb -u adminstrator -H "3dc553ce4b9fd20bd016e098d2d2fd2e"
```
![screenshot](assets/screenshots/Administrator/22.png)

## 🎯 Domain Compromise Achieved

With access as Administrator, I navigated to the desktop and retrieved the root flag, marking the successful full compromise of the domain.

![screenshot](assets/screenshots/Administrator/23.png)

# Pwned
![screenshot](assets/screenshots/Administrator/24.png)

## 🧾 Conclusion

The Administrator machine showcased a realistic domain escalation scenario where improper permission configurations and weak credential management led to full domain compromise. Starting with a low-privileged user, we exploited misconfigured ACLs to pivot between accounts, eventually gaining access to sensitive files. Through careful enumeration, password cracking, and targeted Kerberoasting, we escalated privileges and obtained DCSync rights, enabling us to retrieve the Administrator hash and fully compromise the domain controller.
## 🧯 Mitigation & Defense Strategies

To prevent such attacks in real-world environments, the following measures are recommended:

    Implement the Principle of Least Privilege: Review and restrict unnecessary GenericAll, GenericWrite, and ForceChangePassword permissions in Active Directory.

    Enforce Strong Password Policies: Require complex passwords and regular rotation for all domain users, especially privileged accounts.

    Monitor and Audit AD Changes: Use centralized logging to monitor changes to user permissions and unusual account activities.

    Limit Service Account Privileges: Avoid granting service accounts excessive permissions unless absolutely necessary.

    Secure FTP and Remote Services: Disable unused services like FTP and secure remote access protocols with proper credential management and segmentation.

    Use LAPS: Implement Local Administrator Password Solution (LAPS) to manage local admin credentials securely.

    Detect and Prevent Credential Dumping: Use EDR tools and enable LSASS protection to detect secretsdump-like behavior.



Till next time

#OperationFireball #KillTheLimits #Sniper #SerialKiller #RedTeam #Pentesting #ActiveDirectory
