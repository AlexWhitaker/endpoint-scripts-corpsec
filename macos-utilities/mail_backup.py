import os
import shutil
from datetime import datetime
import mailbox
import email
import json

def backup_mac_mail(backup_dir=None):
    """
    Creates a backup of Mac Mail messages without deleting originals.
    
    Parameters:
    backup_dir (str): Optional custom backup directory path
    """
    # Default mail location on Mac
    mail_dir = os.path.expanduser('~/Library/Mail/V9')  # V9 is for recent MacOS versions
    
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if backup_dir is None:
        backup_dir = os.path.expanduser(f'~/Desktop/MailBackup_{timestamp}')
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    def process_mailbox(mbox_path, relative_path):
        """Process individual .mbox files"""
        try:
            mbox = mailbox.mbox(mbox_path)
            emails = []
            
            for key, msg in enumerate(mbox):
                email_data = {
                    'subject': msg.get('subject', ''),
                    'from': msg.get('from', ''),
                    'to': msg.get('to', ''),
                    'date': msg.get('date', ''),
                    'message_id': msg.get('message-id', ''),
                }
                
                # Save the full email as .eml
                eml_path = os.path.join(backup_dir, relative_path, f'email_{key}.eml')
                os.makedirs(os.path.dirname(eml_path), exist_ok=True)
                
                with open(eml_path, 'w', encoding='utf-8') as f:
                    f.write(msg.as_string())
                
                emails.append(email_data)
            
            # Save metadata for this mailbox
            meta_path = os.path.join(backup_dir, relative_path, 'metadata.json')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(emails, f, indent=2)
                
        except Exception as e:
            print(f"Error processing {mbox_path}: {str(e)}")

    def scan_mail_directory(directory):
        """Recursively scan mail directory for .mbox files"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.mbox'):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(root, mail_dir)
                    process_mailbox(full_path, relative_path)

    try:
        # Start backup process
        print(f"Starting mail backup to: {backup_dir}")
        scan_mail_directory(mail_dir)
        
        # Create a log file
        log_path = os.path.join(backup_dir, 'backup_log.txt')
        with open(log_path, 'w') as f:
            f.write(f"Backup completed at: {datetime.now()}\n")
            f.write(f"Source directory: {mail_dir}\n")
        
        print(f"Backup completed successfully! Files saved to: {backup_dir}")
        return True
        
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        return False

if __name__ == "__main__":
    backup_mac_mail()
