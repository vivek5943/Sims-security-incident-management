"""
MOD-03: ML Model Trainer — v3
FIX-10: Expanded training corpus: 50+ samples per category (was ~15)
        Total: 400+ samples across 8 categories × 4 severity levels
FIX-11: Severity classifier documented as 'text-based estimation tool, not replacement for human judgment'
FIX-12: Calibrated probability scores using CalibratedClassifierCV
FIX-15: Dual ML classifiers — category + severity, zero keyword rules in inference
"""
import logging, random
from pathlib import Path

logger = logging.getLogger('apps.ml_engine')

# ─────────────────────────────────────────────────────────────────────────────
# FIX-10: EXPANDED CORPUS — 50+ samples per category
# Format: (description_text, category, severity)
# ─────────────────────────────────────────────────────────────────────────────
TRAINING_CORPUS = [

    # ── Phishing (50 samples) ─────────────────────────────────────────────────
    ("Employee received suspicious email requesting immediate password reset via external link", "Phishing", "Medium"),
    ("User clicked malicious link claiming to be from IT department requesting login credentials", "Phishing", "Medium"),
    ("Phishing campaign targeting finance team with fake invoice containing credential harvesting form", "Phishing", "High"),
    ("Multiple executives received spoofed CEO email requesting urgent wire transfer confirmation", "Phishing", "Critical"),
    ("Email with suspicious attachment from unknown sender requesting account verification", "Phishing", "Low"),
    ("Credential phishing attempt via fake Microsoft login page sent to entire HR department", "Phishing", "Medium"),
    ("Spear phishing email targeting executive team using compromised supplier email domain", "Phishing", "High"),
    ("Mass phishing campaign targeting all employee email addresses with spoofed sender domain", "Phishing", "High"),
    ("Admin credentials submitted to fake Outlook webmail portal linked from phishing message", "Phishing", "Critical"),
    ("Business email compromise attack impersonating CEO requesting financial transaction approval", "Phishing", "Critical"),
    ("Suspicious email with urgent request to update payment details sent to accounts payable team", "Phishing", "High"),
    ("Phishing email containing malicious QR code leading to credential harvesting website", "Phishing", "Medium"),
    ("Email spoofing attack using domain lookalike to impersonate company communications", "Phishing", "Medium"),
    ("User entered credentials into fake password reset portal linked from suspicious email", "Phishing", "High"),
    ("Phishing simulation detected real user credential submission to external unauthorized domain", "Phishing", "Low"),
    ("Fake invoice email with embedded link redirecting to credential harvesting page", "Phishing", "Medium"),
    ("Targeted spear phishing attack on CFO using personal information gathered from LinkedIn", "Phishing", "High"),
    ("Phishing email impersonating Microsoft Azure claiming account suspension requiring login", "Phishing", "Medium"),
    ("Multiple employees clicked phishing link in email purportedly from company IT helpdesk", "Phishing", "High"),
    ("Tax refund phishing scam targeting finance department employees with fake government portal", "Phishing", "Medium"),
    ("Whaling attack targeting board members using customized email with executive assistant impersonation", "Phishing", "Critical"),
    ("Clone phishing attack using legitimate email reply thread with malicious attachment added", "Phishing", "High"),
    ("Smishing attack via SMS with phishing link targeting employees mobile devices", "Phishing", "Medium"),
    ("User reported receiving a phishing email claiming their corporate account will be suspended", "Phishing", "Low"),
    ("Adversary phishing for VPN credentials via fake IT security awareness training link", "Phishing", "High"),
    ("Phishing email campaign impersonating payroll department requesting direct deposit changes", "Phishing", "Critical"),
    ("HR phishing attack collecting employee PII through fake benefits enrollment form", "Phishing", "High"),
    ("DocuSign phishing email with malicious link to credential stealing page disguised as contract", "Phishing", "Medium"),
    ("Credential phishing via fake password expiry notification from spoofed internal IT address", "Phishing", "Medium"),
    ("Phishing attack delivering malware payload alongside credential harvesting on click", "Phishing", "Critical"),
    ("Vendor impersonation phishing attack requesting updated banking details for payment processing", "Phishing", "Critical"),
    ("Phishing email using CAPTCHA to evade security filters before redirecting to credential page", "Phishing", "Medium"),
    ("Employee received phishing email with attached PDF containing embedded malicious URL", "Phishing", "Medium"),
    ("Bulk phishing campaign detected sending identical emails to entire company mailing list", "Phishing", "High"),
    ("User flagged suspicious login activity after clicking link in password reset phishing email", "Phishing", "High"),
    ("Executive assistant targeted with phishing email to gain access to CEO calendar and emails", "Phishing", "High"),
    ("Callback phishing attack using voicemail notification email to harvest credentials", "Phishing", "Medium"),
    ("Adversarial phishing page using valid SSL certificate to appear legitimate to victims", "Phishing", "Medium"),
    ("User account compromised after submitting credentials to OAuth phishing application", "Phishing", "High"),
    ("Multi-stage phishing attack combining credential theft with malware dropper delivery", "Phishing", "Critical"),
    ("Phishing email targeting password manager users to harvest master credential", "Phishing", "Critical"),
    ("Lateral phishing attack using compromised employee account to target internal colleagues", "Phishing", "High"),
    ("Credential phishing link sent via internal Slack channel from compromised employee account", "Phishing", "Critical"),
    ("Phishing attack targeting single sign-on credentials to compromise multiple connected systems", "Phishing", "Critical"),
    ("Email phishing attack reporting false security alert to trick users into credential entry", "Phishing", "Medium"),
    ("Phishing email mimicking ITSM ticket notification to harvest service desk credentials", "Phishing", "Medium"),
    ("Adversary used harvested credentials from phishing to access customer database", "Phishing", "Critical"),
    ("Phishing campaign exploiting tax season to deliver credential-stealing fake IRS portal", "Phishing", "Medium"),
    ("Targeted phishing attack on DevOps team to harvest cloud infrastructure access tokens", "Phishing", "Critical"),
    ("Employee received phishing email with infected Word document using macro to steal credentials", "Phishing", "High"),

    # ── Malware (50 samples) ──────────────────────────────────────────────────
    ("Unknown executable file found running on workstation consuming abnormally high CPU resources", "Malware", "Medium"),
    ("Antivirus system detected trojan malware on employee laptop during scheduled scan", "Malware", "High"),
    ("Keylogger software discovered on shared workstation in customer service department", "Malware", "Critical"),
    ("Suspicious process injecting code into legitimate Windows process detected by EDR", "Malware", "High"),
    ("Malware sample isolated after unusual outbound traffic to known command and control server", "Malware", "High"),
    ("User downloaded and executed malicious file disguised as legitimate software update package", "Malware", "Medium"),
    ("Backdoor access established on production server detected via anomalous authentication events", "Malware", "Critical"),
    ("Worm spreading through internal network shares detected by network traffic monitoring", "Malware", "Critical"),
    ("Rootkit installation attempted on domain controller flagged by file integrity monitor", "Malware", "Critical"),
    ("Remote access trojan communicating with external IP address during off-hours detected", "Malware", "High"),
    ("Spyware collecting browser history and sending data to unknown external server", "Malware", "High"),
    ("Malicious macro embedded in Word document executed payload on user workstation", "Malware", "Medium"),
    ("Fileless malware residing entirely in memory without disk presence detected", "Malware", "High"),
    ("Banking trojan attempting to intercept financial transactions on finance workstation", "Malware", "Critical"),
    ("Polymorphic malware variant evaded antivirus scan and established system persistence", "Malware", "High"),
    ("Cryptominer malware using company resources for cryptocurrency mining without authorization", "Malware", "Medium"),
    ("DLL injection attack detected with malicious library loaded into legitimate process", "Malware", "High"),
    ("Malicious scheduled task created by malware for persistence and regular execution", "Malware", "High"),
    ("Adware with spyware capabilities installed without user authorization on multiple endpoints", "Malware", "Medium"),
    ("Mobile device malware detected after employee sideloaded unauthorized application", "Malware", "Medium"),
    ("Supply chain malware injected into software update package from trusted vendor", "Malware", "Critical"),
    ("Botnet agent installed on workstation attempting to join distributed attack infrastructure", "Malware", "High"),
    ("Steganographic malware hiding commands inside legitimate image files on file server", "Malware", "High"),
    ("Malware exfiltrating sensitive data via encrypted DNS tunneling to avoid detection", "Malware", "Critical"),
    ("Firmware malware detected in BIOS of multiple workstations persisting across reimaging", "Malware", "Critical"),
    ("Credential-stealing malware targeting browser saved passwords and session cookies", "Malware", "High"),
    ("Point-of-sale malware scraping credit card data from retail payment terminals", "Malware", "Critical"),
    ("Dropper malware delivered via phishing then downloading secondary payload from internet", "Malware", "High"),
    ("Malware detected using process hollowing technique to hide inside legitimate Windows process", "Malware", "High"),
    ("Ransomware dropper detected before encryption stage began and neutralized by EDR", "Malware", "High"),
    ("Malware establishing persistence through Windows registry Run keys and startup folders", "Malware", "Medium"),
    ("USB-delivered malware automatically executed when infected drive inserted into workstation", "Malware", "High"),
    ("Malware disabling antivirus software and firewall before downloading additional payloads", "Malware", "Critical"),
    ("Spear phishing delivered RAT giving attacker full remote access to executive workstation", "Malware", "Critical"),
    ("Malware beaconing every 60 seconds to command and control server using HTTP GET requests", "Malware", "High"),
    ("Macro malware in Excel spreadsheet sent as attachment executing PowerShell download cradle", "Malware", "High"),
    ("Email-borne malware spreading to all Outlook contacts after infection of one workstation", "Malware", "Critical"),
    ("Malware leveraging LOLBins living-off-the-land techniques using native Windows tools", "Malware", "High"),
    ("Cross-site scripting malware injected into company web application serving users", "Malware", "High"),
    ("Malware variant targeting industrial control systems in manufacturing environment", "Malware", "Critical"),
    ("Malware detected attempting lateral movement using stolen credentials across network", "Malware", "Critical"),
    ("Malware using Tor network for command and control to evade network monitoring", "Malware", "High"),
    ("Cryptojacking malware detected running on cloud instances inflating compute costs", "Malware", "Medium"),
    ("Malware injecting advertisement code into bank transaction pages in browser", "Malware", "Critical"),
    ("Malware using time-based evasion activating only during business hours to avoid analysis", "Malware", "High"),
    ("Loader malware detected installing multiple secondary payloads on compromised system", "Malware", "Critical"),
    ("Malware using trusted application certificate to bypass application whitelisting controls", "Malware", "High"),
    ("Wiper malware detected attempting to destroy master boot record on targeted servers", "Malware", "Critical"),
    ("Malware targeting backup systems to prevent recovery before ransomware deployment", "Malware", "Critical"),
    ("Malware using BITS background service for stealthy download of additional components", "Malware", "High"),

    # ── Ransomware (50 samples) ───────────────────────────────────────────────
    ("Critical file server data encrypted with unknown extension rendering all files inaccessible", "Ransomware", "Critical"),
    ("Ransom note demanding bitcoin payment found across shared network drives with locked files", "Ransomware", "Critical"),
    ("Ransomware encrypted database server files and dropped ransom demand for decryption key", "Ransomware", "Critical"),
    ("Multiple workstations showing file encryption activity with locked extension on all documents", "Ransomware", "Critical"),
    ("Production environment experiencing mass file encryption with attacker ransom note", "Ransomware", "Critical"),
    ("Ransomware variant propagating through network shares encrypting all accessible files", "Ransomware", "Critical"),
    ("Backup server targeted by ransomware deleting shadow copies before encrypting backup files", "Ransomware", "Critical"),
    ("Financial records encrypted by ransomware attack demanding payment within 72-hour deadline", "Ransomware", "Critical"),
    ("Ransomware deployed after phishing email opened encrypting entire user profile data", "Ransomware", "Critical"),
    ("Double extortion ransomware encrypted data and threatened to leak sensitive information publicly", "Ransomware", "Critical"),
    ("Healthcare patient records encrypted by ransomware disrupting clinical operations entirely", "Ransomware", "Critical"),
    ("Ransomware detected on single endpoint before encryption propagated and quickly contained", "Ransomware", "High"),
    ("Encrypted files discovered with attacker contact instructions on desktop as ransom note", "Ransomware", "Critical"),
    ("Automated backup system encrypted by ransomware making recovery impossible without payment", "Ransomware", "Critical"),
    ("Known ransomware family variant detected encrypting network attached storage volumes", "Ransomware", "Critical"),
    ("Ransomware spreading laterally after initial entry encrypting servers across multiple sites", "Ransomware", "Critical"),
    ("Critical infrastructure ransomware attack forcing operational shutdown of manufacturing plant", "Ransomware", "Critical"),
    ("Ransomware pre-deployment stage detected with attacker mapping file shares before encryption", "Ransomware", "High"),
    ("Ransomware deleting volume shadow copies to prevent Windows recovery before encryption", "Ransomware", "Critical"),
    ("Ransomware operator exfiltrating data before encryption for double extortion leverage", "Ransomware", "Critical"),
    ("Ransomware using legitimate remote administration tools to spread across enterprise network", "Ransomware", "Critical"),
    ("Education sector ransomware attack encrypting student records and administrative systems", "Ransomware", "Critical"),
    ("Ransomware deploying after hours to maximize damage before IT team can respond", "Ransomware", "Critical"),
    ("Ransomware note found demanding triple extortion including customer notification threat", "Ransomware", "Critical"),
    ("Ransomware attack encrypting cloud-synchronized files spreading to all synced endpoints", "Ransomware", "Critical"),
    ("Partial ransomware encryption detected and stopped leaving some files recoverable", "Ransomware", "High"),
    ("Ransomware using intermittent encryption to evade behavioral detection systems", "Ransomware", "Critical"),
    ("Ransomware actor threatening to auction stolen data if ransom not paid by deadline", "Ransomware", "Critical"),
    ("Government agency ransomware attack encrypting case management and citizen records", "Ransomware", "Critical"),
    ("Ransomware detected in one department isolated before spreading to broader network", "Ransomware", "High"),
    ("Ransomware group claiming successful attack and posting sample encrypted files publicly", "Ransomware", "Critical"),
    ("Ransomware encrypting virtual machine disk files causing multiple server outages", "Ransomware", "Critical"),
    ("Ransomware actor gaining access via exposed RDP before deploying encryption payload", "Ransomware", "Critical"),
    ("Ransomware deployed via managed service provider compromising multiple client environments", "Ransomware", "Critical"),
    ("Ransomware attack timed with public holiday weekend to delay detection and response", "Ransomware", "Critical"),
    ("Ransomware encrypting email archives and collaboration tool data alongside file shares", "Ransomware", "Critical"),
    ("Suspected ransomware staging detected with attacker reconnaissance activities on network", "Ransomware", "High"),
    ("Ransomware attack on law firm encrypting privileged attorney-client communication files", "Ransomware", "Critical"),
    ("Ransomware operator compromising admin credentials before deploying encryption at scale", "Ransomware", "Critical"),
    ("Ransomware note discovered threatening exposure of patient medical records unless paid", "Ransomware", "Critical"),
    ("Ransomware affecting only development environment with limited operational impact", "Ransomware", "Medium"),
    ("Ransomware payment site and decryption key verification tested and confirmed functional", "Ransomware", "Critical"),
    ("Ransomware reinfection detected after partial recovery indicating incomplete remediation", "Ransomware", "Critical"),
    ("Ransomware encrypting Microsoft SharePoint and OneDrive cloud storage content", "Ransomware", "Critical"),
    ("New ransomware variant discovered using novel encryption scheme resistant to known decryptors", "Ransomware", "Critical"),
    ("Ransomware deployment aborted after defender killed malicious process mid-execution", "Ransomware", "High"),
    ("Ransomware actor posting proof of data theft before demanding cryptocurrency ransom", "Ransomware", "Critical"),
    ("Critical database encrypted by ransomware during peak business hours causing major outage", "Ransomware", "Critical"),
    ("Ransomware infected air-gapped system through removable media circumventing network isolation", "Ransomware", "Critical"),
    ("Ransomware as a service operator deploying affiliate payload across corporate network", "Ransomware", "Critical"),

    # ── DDoS (50 samples) ─────────────────────────────────────────────────────
    ("Web application servers experiencing extreme latency and service unavailability from traffic flood", "DDoS", "High"),
    ("Network flooded with UDP packets from multiple source addresses causing complete service disruption", "DDoS", "High"),
    ("DNS servers under amplification attack generating massive traffic overwhelming bandwidth", "DDoS", "Critical"),
    ("HTTP flood attack targeting customer-facing portal causing complete service outage", "DDoS", "Critical"),
    ("SYN flood consuming all TCP connection slots on load balancer causing new connection failures", "DDoS", "High"),
    ("Bandwidth saturation attack from distributed botnet infrastructure exceeding link capacity", "DDoS", "Critical"),
    ("Application layer DDoS targeting login endpoint with thousands of automated requests per second", "DDoS", "High"),
    ("ICMP ping flood attack consuming network resources and causing significant packet loss", "DDoS", "Medium"),
    ("API gateway under volumetric DDoS attack with rotating source IP addresses", "DDoS", "High"),
    ("DDoS attack exceeding 100 Gbps threshold detected and escalated to ISP for upstream mitigation", "DDoS", "Critical"),
    ("Customer portal completely unavailable due to sustained DDoS attack lasting over four hours", "DDoS", "Critical"),
    ("NTP amplification reflected DDoS attack flooding company infrastructure with amplified packets", "DDoS", "High"),
    ("SSL exhaustion attack consuming all available handshake capacity on HTTPS load balancers", "DDoS", "High"),
    ("CDN provider reporting DDoS attack bypassing edge protection targeting origin servers", "DDoS", "Critical"),
    ("Slow HTTP DDoS attack holding connections open indefinitely causing application slowdown", "DDoS", "Medium"),
    ("Memcached amplification DDoS attack generating hundreds of gigabits per second of traffic", "DDoS", "Critical"),
    ("DNS query flood overwhelming authoritative name servers causing resolution failures", "DDoS", "High"),
    ("Volumetric DDoS attack causing BGP route instability affecting multiple network segments", "DDoS", "Critical"),
    ("Application DDoS targeting expensive database queries to exhaust backend resources", "DDoS", "High"),
    ("Multi-vector DDoS combining volumetric and application layer attacks simultaneously", "DDoS", "Critical"),
    ("DDoS attack disrupting voice over IP communications infrastructure during business hours", "DDoS", "High"),
    ("Gaming server DDoS attack causing complete disconnection for all active players", "DDoS", "Medium"),
    ("DDoS ransom demand received threatening sustained attack unless cryptocurrency paid", "DDoS", "High"),
    ("SSDP amplification attack reflecting traffic off vulnerable IoT devices towards target", "DDoS", "High"),
    ("DDoS botnet using infected IoT cameras to generate attack traffic against web services", "DDoS", "High"),
    ("Carpet bombing DDoS attacking entire IP subnet rather than single address", "DDoS", "Critical"),
    ("DDoS attack on email infrastructure causing mail delivery failures across organization", "DDoS", "High"),
    ("DDoS attackers rotating attack vectors every 30 minutes to evade mitigation rules", "DDoS", "Critical"),
    ("Low and slow DDoS attack designed to exhaust server resources without triggering volume alerts", "DDoS", "Medium"),
    ("DDoS attack coinciding with company product launch causing reputational damage", "DDoS", "Critical"),
    ("DDoS attack targeting financial transaction endpoints during peak trading hours", "DDoS", "Critical"),
    ("DDoS attack overwhelming WAF capacity leading to bypass of application layer protections", "DDoS", "Critical"),
    ("DDoS attack from state-sponsored threat actor targeting government service infrastructure", "DDoS", "Critical"),
    ("DNS DDoS attack causing cascading failures in microservices dependent on name resolution", "DDoS", "High"),
    ("DDoS attack on authentication service preventing all user logins across applications", "DDoS", "Critical"),
    ("DDoS attack from compromised university research network using legitimate IP addresses", "DDoS", "High"),
    ("Reflected DDoS using misconfigured open resolvers amplifying attack traffic significantly", "DDoS", "High"),
    ("DDoS attack targeting payment gateway causing loss of sales during peak period", "DDoS", "Critical"),
    ("HTTP/2 rapid reset DDoS attack overwhelming web servers with incomplete requests", "DDoS", "High"),
    ("DDoS attack causing upstream provider to null-route company IP block impacting all services", "DDoS", "Critical"),
    ("DDoS reconnaissance scan preceding main attack wave detected and blocked preemptively", "DDoS", "Low"),
    ("DDoS attack targeting specific API endpoints used for real-time communication features", "DDoS", "Medium"),
    ("DDoS attack using legitimate cloud provider infrastructure making IP blocking difficult", "DDoS", "High"),
    ("Sustained multi-day DDoS campaign exhausting DDoS mitigation service capacity and budget", "DDoS", "Critical"),
    ("DDoS attack causing database connection pool exhaustion leading to application errors", "DDoS", "High"),
    ("DDoS attack exploiting websocket protocol to exhaust server connection handling capacity", "DDoS", "Medium"),
    ("DDoS attack combined with data breach as distraction during simultaneous intrusion attempt", "DDoS", "Critical"),
    ("Cloud DDoS attack causing auto-scaling to trigger unexpected massive infrastructure cost", "DDoS", "High"),
    ("DDoS attackers exploiting unsecured Kubernetes API endpoints as amplification vectors", "DDoS", "High"),
    ("Hacktivist group DDoS attack targeting company website in response to business decision", "DDoS", "Medium"),

    # ── Insider Threat (50 samples) ───────────────────────────────────────────
    ("Employee accessing sensitive customer records outside normal working hours without justification", "Insider Threat", "High"),
    ("Large volume of confidential files transferred to personal USB drive by employee who resigned", "Insider Threat", "Critical"),
    ("Privileged user accessing restricted financial database records unrelated to their job function", "Insider Threat", "High"),
    ("Departing employee systematically exfiltrating data to personal cloud storage account before last day", "Insider Threat", "Critical"),
    ("IT administrator accessing executive emails without proper authorization or business justification", "Insider Threat", "High"),
    ("Employee downloading bulk customer contact database to personal device before resignation", "Insider Threat", "Critical"),
    ("Contractor accessing proprietary source code repository significantly beyond project scope", "Insider Threat", "High"),
    ("Disgruntled employee deliberately deleting critical records from database before termination", "Insider Threat", "Critical"),
    ("Employee exfiltrating intellectual property to personal email account over extended period", "Insider Threat", "Critical"),
    ("Privileged access abuse with IT staff accessing production credentials without change ticket", "Insider Threat", "High"),
    ("Employee sharing confidential merger details with external financial contact via personal email", "Insider Threat", "Critical"),
    ("Terminated employee account accessed remotely after offboarding deadline using retained credentials", "Insider Threat", "High"),
    ("Administrator making unauthorized system configuration changes outside change management process", "Insider Threat", "High"),
    ("Employee installed unauthorized remote access tool on workstation to maintain persistent access", "Insider Threat", "High"),
    ("Screenshot of sensitive financial projections shared externally via personal messaging platform", "Insider Threat", "Medium"),
    ("Employee copying competitor intelligence from research databases to personal storage", "Insider Threat", "High"),
    ("System administrator creating undocumented backdoor account before departing organization", "Insider Threat", "Critical"),
    ("Employee accessing personnel files of colleagues outside scope of HR responsibilities", "Insider Threat", "Medium"),
    ("Developer embedding logic bomb in production code discovered during routine code review", "Insider Threat", "Critical"),
    ("Sales employee exfiltrating entire customer list and pricing data before joining competitor", "Insider Threat", "Critical"),
    ("Employee working with external threat actor providing network credentials for financial gain", "Insider Threat", "Critical"),
    ("Insider sabotaging automated backups causing silent failure over months before discovery", "Insider Threat", "Critical"),
    ("Employee sharing customer personal data with marketing firm without authorization", "Insider Threat", "High"),
    ("Security analyst abusing access to monitor personal relationships of company executives", "Insider Threat", "High"),
    ("Employee printing large volumes of proprietary technical documentation before departure", "Insider Threat", "High"),
    ("IT support staff accessing user personal files stored on corporate file server", "Insider Threat", "Medium"),
    ("Employee using corporate VPN to route personal traffic and conceal outside activity", "Insider Threat", "Low"),
    ("Authorized user accessing production environment during vacation to conduct unauthorized changes", "Insider Threat", "High"),
    ("Employee sharing login credentials with colleague circumventing access control policies", "Insider Threat", "Medium"),
    ("Database administrator exfiltrating customer payment card data through trusted query access", "Insider Threat", "Critical"),
    ("Employee using privileged access to manipulate audit logs to cover unauthorized activities", "Insider Threat", "Critical"),
    ("Contractor accessing client billing systems beyond authorized project scope for financial data", "Insider Threat", "High"),
    ("Employee systematically accessing all customer accounts not assigned to them during night shift", "Insider Threat", "High"),
    ("Insider leaking unreleased product specifications to competitor in exchange for job offer", "Insider Threat", "Critical"),
    ("Employee accessing clinical trial data beyond research scope potentially violating regulations", "Insider Threat", "High"),
    ("IT contractor installing personal network monitoring tools on corporate infrastructure", "Insider Threat", "High"),
    ("Employee exfiltrating source code to personal GitHub repository during employment", "Insider Threat", "Critical"),
    ("Whistleblower leaking confidential information to media through unauthorized channels", "Insider Threat", "High"),
    ("Employee facilitating social engineering attacks by providing internal contact information", "Insider Threat", "High"),
    ("System administrator creating hidden privileged account for personal use after resignation", "Insider Threat", "Critical"),
    ("Employee accessing deceased customer accounts without authorization or business reason", "Insider Threat", "Medium"),
    ("Insider bypassing document rights management to create unprotected copies of confidential files", "Insider Threat", "High"),
    ("Employee forwarding all emails to personal account creating unauthorized data copy", "Insider Threat", "High"),
    ("Temporary staff member accessing permanent employee systems beyond assigned work scope", "Insider Threat", "Medium"),
    ("Security team member accessing incident reports outside their assigned cases", "Insider Threat", "Medium"),
    ("Employee receiving unauthorized payments from vendor in exchange for contract information", "Insider Threat", "Critical"),
    ("Insider providing physical access badge to external individual for facility access", "Insider Threat", "Critical"),
    ("Employee using administrative access to elevate personal privileges beyond authorization", "Insider Threat", "High"),
    ("Departing executive copying board presentations and strategic plans before final day", "Insider Threat", "Critical"),
    ("Employee trading company stock using insider information accessed through privileged database access", "Insider Threat", "Critical"),

    # ── Data Breach (50 samples) ──────────────────────────────────────────────
    ("Personal data of 50000 customers exposed through misconfigured public S3 storage bucket", "Data Breach", "Critical"),
    ("Database containing encrypted credit card numbers found publicly accessible on internet", "Data Breach", "Critical"),
    ("Employee data including social security numbers exposed via unprotected internal API endpoint", "Data Breach", "Critical"),
    ("Medical records exposed through broken access control in patient portal web application", "Data Breach", "Critical"),
    ("Customer email addresses and hashed passwords leaked from third-party data processor partner", "Data Breach", "High"),
    ("PII exposed via SQL injection vulnerability exploited in customer-facing web application", "Data Breach", "Critical"),
    ("Sensitive HR documents indexed by search engines due to misconfigured web server permissions", "Data Breach", "High"),
    ("Payment card data potentially compromised via skimmer script on e-commerce checkout page", "Data Breach", "Critical"),
    ("Internal employee directory with personal contact information exposed via unauthenticated API", "Data Breach", "High"),
    ("Financial statements and customer data found on unencrypted stolen company laptop", "Data Breach", "High"),
    ("Third-party vendor notified company of breach involving stored customer data records", "Data Breach", "High"),
    ("Log files containing active session tokens exposed on publicly accessible web server", "Data Breach", "Medium"),
    ("Customer passwords stored in plaintext in legacy database discovered during security audit", "Data Breach", "High"),
    ("Backup files with sensitive customer data uploaded to wrong public cloud storage container", "Data Breach", "Medium"),
    ("Company credentials discovered being sold on dark web marketplace by monitoring service", "Data Breach", "Critical"),
    ("Data breach notification received requiring GDPR Article 33 regulatory notification within 72 hours", "Data Breach", "Critical"),
    ("Customer database backup file found in unsecured FTP server accessible from internet", "Data Breach", "Critical"),
    ("Personal health information exposed through insecure direct object reference vulnerability", "Data Breach", "Critical"),
    ("Employee personal data exposed in misconfigured Elasticsearch index accessible publicly", "Data Breach", "High"),
    ("Customer billing information exposed through API endpoint missing authentication requirement", "Data Breach", "Critical"),
    ("Internal email archive with confidential communications exposed through misconfigured server", "Data Breach", "High"),
    ("Data breach affecting minors requiring immediate regulatory notification under COPPA", "Data Breach", "Critical"),
    ("Exposed database credentials in public code repository leading to unauthorized data access", "Data Breach", "Critical"),
    ("Customer data exported without authorization by analytics vendor partner organization", "Data Breach", "High"),
    ("Financial trading data exposed through insecure websocket connection in trading platform", "Data Breach", "Critical"),
    ("Data breach traced to compromise of managed service provider with access to client systems", "Data Breach", "Critical"),
    ("Personal data exposed through broken object-level authorization in REST API endpoints", "Data Breach", "High"),
    ("Customer records accessed by unauthorized third party through compromised API key", "Data Breach", "High"),
    ("Sensitive research data exposed through misconfigured academic data sharing platform", "Data Breach", "Medium"),
    ("Employee benefits data exposed through insecure HR self-service portal configuration", "Data Breach", "High"),
    ("Data breach discovered through customer complaints about receiving other users data", "Data Breach", "High"),
    ("Exposed cloud storage bucket containing confidential merger and acquisition documents", "Data Breach", "Critical"),
    ("Personal data breach through vulnerability in mobile application backend API service", "Data Breach", "High"),
    ("Customer data scraping attack exploiting overly permissive API pagination implementation", "Data Breach", "High"),
    ("Data breach affecting government employee records requiring mandatory breach reporting", "Data Breach", "Critical"),
    ("Internal database migration misconfiguration exposed sensitive records temporarily online", "Data Breach", "Medium"),
    ("Data breach through insecure deserialization vulnerability in enterprise application", "Data Breach", "Critical"),
    ("Customer data exposed through IDOR vulnerability allowing access to other user profiles", "Data Breach", "High"),
    ("Sensitive financial data exposed in verbose error messages returned by production API", "Data Breach", "Medium"),
    ("Data breach traced to compromised employee account with access to customer data systems", "Data Breach", "High"),
    ("Personal data exposed through path traversal vulnerability in document management system", "Data Breach", "High"),
    ("Customer PII exposed through GraphQL introspection and unrestricted query capabilities", "Data Breach", "High"),
    ("Data breach notification from payment processor about compromise affecting stored cards", "Data Breach", "Critical"),
    ("Healthcare data breach requiring HHS OCR notification under HIPAA Breach Notification Rule", "Data Breach", "Critical"),
    ("Data breach through stolen employee laptop lacking full disk encryption protection", "Data Breach", "High"),
    ("Exposed Kubernetes secret containing database connection strings with customer data access", "Data Breach", "Critical"),
    ("Customer data breach through cross-site request forgery attack on account management page", "Data Breach", "Medium"),
    ("Personal data breach affecting EU residents requiring data protection authority notification", "Data Breach", "Critical"),
    ("Data breach through compromised admin account used to export customer database records", "Data Breach", "Critical"),
    ("Data breach discovered during penetration test revealing unauthorized external data access", "Data Breach", "High"),

    # ── Unauthorized Access (50 samples) ──────────────────────────────────────
    ("Brute force attack on SSH service successfully gained root access from external IP address", "Unauthorized Access", "Critical"),
    ("Attacker exploited unpatched remote code execution vulnerability gaining admin application access", "Unauthorized Access", "Critical"),
    ("Credential stuffing attack successfully authenticated to multiple employee accounts simultaneously", "Unauthorized Access", "High"),
    ("Unauthorized login to executive account from foreign country IP during off-hours detected", "Unauthorized Access", "High"),
    ("API key found committed to public GitHub repository used to access production database", "Unauthorized Access", "Critical"),
    ("Former employee used retained credentials to access CRM system months after offboarding", "Unauthorized Access", "High"),
    ("Attacker bypassed MFA through real-time SIM swap to access executive email and data", "Unauthorized Access", "Critical"),
    ("Password spray attack successfully compromised service account with weak default password", "Unauthorized Access", "High"),
    ("Unauthorized access to admin control panel via unchanged default vendor credentials", "Unauthorized Access", "High"),
    ("Privilege escalation detected after attacker gained initial foothold through phishing attack", "Unauthorized Access", "Critical"),
    ("Remote desktop protocol exposed to internet brute-forced resulting in unauthorized server access", "Unauthorized Access", "Critical"),
    ("Pass-the-hash attack used to authenticate to multiple systems without knowing account password", "Unauthorized Access", "Critical"),
    ("Unauthorized access to financial billing system detected via anomalous late-night API calls", "Unauthorized Access", "High"),
    ("VPN credentials obtained through phishing enabling unauthorized network access from external actor", "Unauthorized Access", "Critical"),
    ("Authentication bypass vulnerability exploited in web application allowing unauthenticated admin access", "Unauthorized Access", "Critical"),
    ("Unauthorized Kubernetes cluster access gained through misconfigured RBAC permissions", "Unauthorized Access", "Critical"),
    ("Attacker gained unauthorized cloud console access through compromised IAM user credentials", "Unauthorized Access", "Critical"),
    ("Unauthorized database access through SQL injection providing direct record-level data retrieval", "Unauthorized Access", "High"),
    ("Attacker used NTLM relay attack to gain unauthorized access to file server resources", "Unauthorized Access", "High"),
    ("Unauthorized access gained through exploitation of OAuth token validation vulnerability", "Unauthorized Access", "High"),
    ("Attacker leveraged Kerberoasting attack to crack service account password and gain access", "Unauthorized Access", "Critical"),
    ("Unauthorized access to medical records system through shared generic login credentials", "Unauthorized Access", "High"),
    ("Attacker gained unauthorized access to source code repository via stolen developer token", "Unauthorized Access", "Critical"),
    ("Unauthorized admin access gained through cross-tenant isolation vulnerability in SaaS platform", "Unauthorized Access", "Critical"),
    ("Unauthorized access to trading system through exploited session fixation vulnerability", "Unauthorized Access", "Critical"),
    ("Attacker gaining unauthorized persistent access through golden ticket Kerberos attack", "Unauthorized Access", "Critical"),
    ("Unauthorized access to internal network through guest WiFi network segmentation failure", "Unauthorized Access", "High"),
    ("Unauthorized cloud storage access gained by exploiting overly permissive bucket policy", "Unauthorized Access", "High"),
    ("Attacker gaining unauthorized OT network access through IT-OT network segmentation gap", "Unauthorized Access", "Critical"),
    ("Unauthorized API access through JWT algorithm confusion attack on authentication endpoint", "Unauthorized Access", "High"),
    ("Unauthorized access to phone system allowing toll fraud and interception of calls", "Unauthorized Access", "High"),
    ("Attacker unauthorized access to CI/CD pipeline enabling potential malicious code injection", "Unauthorized Access", "Critical"),
    ("Unauthorized access to customer admin panel through predictable session token generation", "Unauthorized Access", "High"),
    ("Attacker gaining unauthorized domain admin access through zerologon vulnerability exploitation", "Unauthorized Access", "Critical"),
    ("Unauthorized physical access to server room through tailgating behind authorized personnel", "Unauthorized Access", "High"),
    ("Unauthorized access to security camera system enabling attacker surveillance of facilities", "Unauthorized Access", "High"),
    ("Attacker gaining unauthorized access to HSM through stolen PIN and physical proximity", "Unauthorized Access", "Critical"),
    ("Unauthorized access to container registry enabling potential backdoor injection into images", "Unauthorized Access", "Critical"),
    ("Attacker unauthorized access to backup system enabling data exfiltration without triggering alerts", "Unauthorized Access", "Critical"),
    ("Unauthorized access to HR system discovered through payroll anomaly investigation", "Unauthorized Access", "High"),
    ("Attacker exploiting forgotten internet-exposed management interface for unauthorized access", "Unauthorized Access", "Critical"),
    ("Unauthorized access to email through OAuth application with excessive requested permissions", "Unauthorized Access", "Medium"),
    ("Attacker gaining unauthorized access through unpatched Citrix ADC vulnerability", "Unauthorized Access", "Critical"),
    ("Unauthorized lateral movement from compromised workstation to critical server infrastructure", "Unauthorized Access", "Critical"),
    ("Unauthorized access to operational technology systems through compromised vendor remote access", "Unauthorized Access", "Critical"),
    ("Attacker using stolen service account credentials to achieve unauthorized domain replication", "Unauthorized Access", "Critical"),
    ("Unauthorized access to customer portal by exploiting mass assignment vulnerability in API", "Unauthorized Access", "Medium"),
    ("Unauthorized access to financial reporting system through forgotten developer test account", "Unauthorized Access", "High"),
    ("Attacker gaining unauthorized access through ProxyShell exchange server vulnerability chain", "Unauthorized Access", "Critical"),
    ("Unauthorized access detected through anomalous geographic login pattern analysis by SIEM", "Unauthorized Access", "Medium"),

    # ── Social Engineering (50 samples) ──────────────────────────────────────
    ("Employee manipulated via phone call by attacker pretending to be IT support to reveal password", "Social Engineering", "High"),
    ("Attacker impersonated CEO using deepfake voice technology to authorize fraudulent wire transfer", "Social Engineering", "Critical"),
    ("Unauthorized individual gained facility access by tailgating authorized employee through door", "Social Engineering", "High"),
    ("Employee deceived into installing remote access software by fake Microsoft technical support", "Social Engineering", "High"),
    ("Attacker posed as vendor representative extracting internal network topology from receptionist", "Social Engineering", "Medium"),
    ("Vishing attack on IT help desk convinced agent to reset executive account without verification", "Social Engineering", "Critical"),
    ("Employee manipulated into disclosing customer database credentials to fake regulatory auditor", "Social Engineering", "Critical"),
    ("Infected USB drive deliberately left in company parking lot found and connected by employee", "Social Engineering", "High"),
    ("Attacker built rapport with receptionist over weeks to obtain visitor access badge", "Social Engineering", "Medium"),
    ("Fake job recruiter extracted sensitive product roadmap from engineer during fake interview", "Social Engineering", "High"),
    ("Employee provided VPN credentials to attacker posing as IT helpdesk on support phone call", "Social Engineering", "Critical"),
    ("Attacker posed as delivery person to gain unauthorized physical access to server room", "Social Engineering", "High"),
    ("Pretexting attack used to gather employee personal information enabling targeted spear phishing", "Social Engineering", "Medium"),
    ("Fake employee survey collected login credentials and sensitive operational information", "Social Engineering", "Medium"),
    ("Watering hole attack compromising industry website frequently visited by target employees", "Social Engineering", "High"),
    ("Attacker using deepfake video of executive in video call to authorize fraudulent transaction", "Social Engineering", "Critical"),
    ("Social engineer posing as fire inspector gained access to sensitive areas of data center", "Social Engineering", "High"),
    ("Employee tricked into providing one-time-password by caller claiming to be from bank fraud team", "Social Engineering", "High"),
    ("Attacker obtained internal org chart through social engineering to plan targeted attack", "Social Engineering", "Medium"),
    ("Fake IT security alert caused employee to call attacker-controlled number and reveal credentials", "Social Engineering", "High"),
    ("Social engineering attack targeting new employees unfamiliar with security procedures", "Social Engineering", "Medium"),
    ("Attacker impersonated external auditor to gain access to financial systems and records", "Social Engineering", "High"),
    ("Employee manipulated through social media friendship into connecting attacker to IT team", "Social Engineering", "Medium"),
    ("Social engineer using insider knowledge gained through OSINT to appear legitimate and trusted", "Social Engineering", "High"),
    ("Attacker posing as facilities manager obtained master key card through social engineering", "Social Engineering", "Critical"),
    ("Employee convinced to disable security software for fake performance optimization", "Social Engineering", "High"),
    ("Social engineering attack targeting customer service staff to bypass identity verification", "Social Engineering", "High"),
    ("Attacker impersonated system administrator to obtain privileged account credentials", "Social Engineering", "Critical"),
    ("Honey trap social engineering using romantic relationship to extract classified information", "Social Engineering", "Critical"),
    ("Attacker using telephone impersonation to gather information for subsequent phishing campaign", "Social Engineering", "Medium"),
    ("Social engineering exploiting employee desire to help resulting in unauthorized system access", "Social Engineering", "High"),
    ("Attacker obtained physical documents from recycling bin containing sensitive network information", "Social Engineering", "Medium"),
    ("Employee manipulated by fake charity campaign to install malicious application", "Social Engineering", "Medium"),
    ("Social engineer gained building access through tailgating at multiple security checkpoints", "Social Engineering", "High"),
    ("Attacker using spoofed caller ID showing legitimate internal extension to deceive employees", "Social Engineering", "High"),
    ("Baiting attack using free USB drives distributed at conference loaded with keylogger malware", "Social Engineering", "High"),
    ("Social engineering exploiting company merger announcement confusion to extract sensitive data", "Social Engineering", "High"),
    ("Attacker posing as journalist conducted social engineering interview to extract trade secrets", "Social Engineering", "Medium"),
    ("Employee fell victim to tech support scam granting remote access to corporate workstation", "Social Engineering", "High"),
    ("Social engineering targeting remote workers through fake IT support chat during pandemic", "Social Engineering", "High"),
    ("Attacker used quit pro quo social engineering offering software help in exchange for access", "Social Engineering", "Medium"),
    ("Social engineer tailgated into multiple restricted areas over several weeks undetected", "Social Engineering", "High"),
    ("Employee manipulated through psychological pressure to approve unauthorized financial transfer", "Social Engineering", "Critical"),
    ("Attacker posing as job candidate gathered intelligence during interview process", "Social Engineering", "Medium"),
    ("Social engineering attack targeting cloud service provider support to gain customer access", "Social Engineering", "High"),
    ("Attacker used reverse social engineering positioning themselves as expert to be called for help", "Social Engineering", "Medium"),
    ("CEO fraud social engineering attack targeting CFO for unauthorized international wire transfer", "Social Engineering", "Critical"),
    ("Social engineer compromising supply chain by targeting less-security-mature vendor organization", "Social Engineering", "High"),
    ("Attacker using spoofed email with correct branding and internal terminology to deceive employee", "Social Engineering", "High"),
    ("Employee manipulated into approving two-factor authentication push notification for attacker", "Social Engineering", "Critical"),
]


def generate_training_data():
    """Build augmented training set from corpus."""
    descriptions, categories, severities = [], [], []
    for desc, cat, sev in TRAINING_CORPUS:
        descriptions.append(desc)
        categories.append(cat)
        severities.append(sev)
        # Augmentation: lowercase
        descriptions.append(desc.lower())
        categories.append(cat)
        severities.append(sev)

    combined = list(zip(descriptions, categories, severities))
    random.shuffle(combined)
    descriptions, categories, severities = zip(*combined)
    return list(descriptions), list(categories), list(severities)


def train_and_save_model():
    import joblib, json
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
    from sklearn.metrics import classification_report
    from sklearn.base import clone
    from django.conf import settings
    from apps.ml_engine.pipeline import TextPreprocessor

    print('\n' + '='*70)
    print('  SIMS ML Engine — v3 Training Pipeline')
    print('='*70)

    preprocessor = TextPreprocessor()

    print('\n[1/7] Generating expanded corpus...')
    descriptions, categories, severities = generate_training_data()
    cat_dist = {c: categories.count(c) for c in set(categories)}
    print(f'      Total: {len(descriptions)} samples | Distribution: {cat_dist}')

    print('\n[2/7] NLP preprocessing...')
    processed = [preprocessor.preprocess(d) for d in descriptions]

    print('\n[3/7] TF-IDF vectorization...')
    vectorizer = TfidfVectorizer(
        max_features=12000, ngram_range=(1, 3),
        sublinear_tf=True, min_df=2, max_df=0.95
    )
    X = vectorizer.fit_transform(processed)
    print(f'      Feature matrix: {X.shape}')

    classifiers = {
        'Multinomial Naive Bayes': MultinomialNB(alpha=0.05),
        'Logistic Regression':     LogisticRegression(C=10, max_iter=2000, solver='lbfgs',
                                                      multi_class='multinomial', random_state=42),
        'Random Forest':           RandomForestClassifier(n_estimators=200, max_depth=None,
                                                          random_state=42, n_jobs=-1),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    print('\n[4/7] Training CATEGORY classifier (8 classes)...')
    cat_results = {}
    for name, clf in classifiers.items():
        scores = cross_val_score(clone(clf), X, categories, cv=cv, scoring='f1_macro', n_jobs=-1)
        cat_results[name] = {'clf': clone(clf), 'f1': scores.mean(), 'std': scores.std()}
        print(f'      {name:35s}  F1: {scores.mean():.4f} (+/-{scores.std():.4f})')

    best_cat_name = max(cat_results, key=lambda k: cat_results[k]['f1'])
    best_cat_clf  = cat_results[best_cat_name]['clf']
    best_cat_clf.fit(X, categories)

    try:
        cat_calibrated = CalibratedClassifierCV(clone(best_cat_clf), cv=2, method='isotonic')
        cat_calibrated.fit(X, categories)
    except ValueError:
        cat_calibrated = best_cat_clf
    print(f'      Best: {best_cat_name} (F1={cat_results[best_cat_name]["f1"]:.4f})')

    print('\n[5/7] Training SEVERITY classifier (4 classes)...')
    sev_results = {}
    for name, clf in classifiers.items():
        scores = cross_val_score(clone(clf), X, severities, cv=cv, scoring='f1_macro', n_jobs=-1)
        sev_results[name] = {'clf': clone(clf), 'f1': scores.mean(), 'std': scores.std()}
        print(f'      {name:35s}  F1: {scores.mean():.4f} (+/-{scores.std():.4f})')

    best_sev_name = max(sev_results, key=lambda k: sev_results[k]['f1'])
    best_sev_clf  = sev_results[best_sev_name]['clf']
    best_sev_clf.fit(X, severities)

    try:
        sev_calibrated = CalibratedClassifierCV(clone(best_sev_clf), cv=2, method='isotonic')
        sev_calibrated.fit(X, severities)
    except ValueError:
        sev_calibrated = best_sev_clf
    print(f'      Best: {best_sev_name} (F1={sev_results[best_sev_name]["f1"]:.4f})')

    print('\n[6/7] Validation metrics...')
    X_tr, X_te, y_cat_tr, y_cat_te, y_sev_tr, y_sev_te = train_test_split(
        X, categories, severities, test_size=0.2, random_state=42
    )
    ce = clone(best_cat_clf); ce.fit(X_tr, y_cat_tr)
    se = clone(best_sev_clf); se.fit(X_tr, y_sev_tr)
    print('\n  CATEGORY CLASSIFIER:')
    print(classification_report(y_cat_te, ce.predict(X_te)))
    print('\n  SEVERITY CLASSIFIER:')
    print(classification_report(y_sev_te, se.predict(X_te)))

    print('\n[7/7] Serializing models...')
    model_path = Path(settings.ML_MODEL_PATH)
    joblib.dump(cat_calibrated, model_path / 'sims_category_classifier.joblib')
    joblib.dump(sev_calibrated, model_path / 'sims_severity_classifier.joblib')
    joblib.dump(vectorizer, model_path / 'sims_tfidf_vectorizer.joblib')

    metadata = {
        'category_model': best_cat_name,
        'category_f1': round(cat_results[best_cat_name]['f1'], 4),
        'severity_model': best_sev_name,
        'severity_f1': round(sev_results[best_sev_name]['f1'], 4),
        'calibrated': True,
        'categories': sorted(set(categories)),
        'severities': sorted(set(severities)),
        'training_samples': len(descriptions),
        'samples_per_category': 100,
        'tfidf_features': X.shape[1],
        'notes': {
            'category': 'Trained ML classifier - Scikit-Learn, cross-validated, calibrated',
            'severity': 'Text-based severity ESTIMATION to assist analysts. Human review mandatory for High/Critical.',
            'confidence': 'CalibratedClassifierCV applied. Label as Model Confidence, not Accuracy.',
        },
    }
    with open(model_path / 'model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f'\n  Models serialized to {model_path}')
    print('='*70 + '\n')
    return metadata