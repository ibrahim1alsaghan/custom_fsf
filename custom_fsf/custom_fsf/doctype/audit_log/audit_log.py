# apps/custom_fsf/custom_fsf/custom_fsf/doctype/audit_log/audit_log.py

"""
Audit Log System for FSF Custom App

This module provides comprehensive audit logging functionality that tracks all document 
changes in the system for compliance and accountability purposes. It captures insert, 
update, delete operations along with user information, IP addresses, and detailed 
change tracking.

Key Features:
- Automatic logging of all document operations
- Detailed change tracking (before/after values)
- User-friendly formatting for child table changes
- Security controls to prevent tampering
- Export and summary functionality
"""

import re
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_to_date, format_datetime, format_date
from frappe.model import no_value_fields, table_fields


# ---------- CONFIGURATION ----------

# Action types that the audit log system recognizes and can process
ALLOWED_ACTIONS = {
    "Insert",           # Document creation
    "Update",           # Document modification  
    "Delete",           # Document deletion
    "Workflow",         # Workflow state changes
    "Permission Change" # Permission modifications
}

# Document types that should never be audited to prevent infinite loops and noise
# These are typically system-generated or logging documents themselves
IGNORED_DOCTYPES = {
    "Audit Log",           # Prevent audit logs of audit logs (infinite loop)
    "Version",             # Frappe's built-in versioning system
    "Activity Log",        # General activity tracking
    "Access Log",          # Login/access tracking  
    "Error Log",           # System error logs
    "Scheduled Job Log",   # Background job logs
    "Background Job",      # Async job records
    "Comment",             # User comments/notes
    "Installed Applications", # App installation records
    "System Console",      # Console command logs
    "Patch Log",           # Database migration logs
    "Module Def",          # Module definition records
    "DocType",             # DocType structure changes
    "Custom Field",        # Custom field definitions
    "Property Setter",     # Property overrides
}

# System fields that are automatically managed and don't represent user changes
SYSTEM_FIELDS = {
    "modified", "modified_by", "creation", "owner", "docstatus",
    "idx", "parent", "parentfield", "parenttype", "doctype",
    "amended_from", "amendment_date", "amended_by"
}

# Fields that should be completely ignored even if they change values
IGNORED_FIELDS = {
    "modified", "modified_by", "creation", "owner", "idx",
    "parent", "parentfield", "parenttype", "doctype", "name",
    "amended_from", "amendment_date", "amended_by",
    "last_active", "last_known_versions", "last_ip", "last_login"
}

# Field types that contain large text and should not be tracked for performance
BLACKLISTED_FIELDS = ["Markdown Editor", "Text Editor", "Code", "HTML Editor"]


# ---------- MAIN AUDIT LOG CLASS ----------

class AuditLog(Document):
    """
    Main Audit Log document class that handles audit log records.
    
    This class enforces security controls to prevent tampering with audit logs
    and provides methods for data retrieval and formatting.
    """
    
    def before_insert(self):
        """
        Security Control: Prevent manual creation of audit logs.
        
        Only the audit system itself should create audit logs to maintain integrity.
        Users cannot manually create audit log entries through the UI or API.
        """
        if not frappe.flags.in_audit_log:
            frappe.throw(_("Audit logs cannot be created manually for security reasons."))
    
    def before_update(self):
        """
        Security Control: Prevent modification of existing audit logs.
        
        Once created, audit logs should be immutable to maintain audit trail integrity.
        Only users with specific write permissions can modify audit logs.
        """
        if not frappe.has_permission("Audit Log", "write", user=frappe.session.user):
            frappe.throw(_("Audit logs cannot be modified for security reasons."))
    
    def before_delete(self):
        """
        Security Control: Prevent deletion of audit logs.
        
        Audit logs should never be deleted to maintain complete audit trail.
        Use archival processes instead of deletion for old logs.
        """
        frappe.throw(_("Audit logs cannot be deleted. Use archival instead."))
    
    def validate(self):
        """
        Data Validation: Ensure audit log integrity before saving.
        
        Validates that required fields are present and sets default values
        for missing timestamps. This ensures all audit logs have consistent
        and complete information.
        """
        # Set current timestamp if not provided
        if not self.timestamp:
            self.timestamp = frappe.utils.now_datetime()
        
        # Validate required fields
        if not self.user:
            frappe.throw(_("User field is required."))
        
        if not self.action_type:
            frappe.throw(_("Action type is required."))
    
    def get_data(self):
        """
        Data Retrieval: Parse JSON data from changed_data field.
        
        Returns:
            dict: Parsed JSON data containing change information, or empty dict if parsing fails
            
        This method safely parses the JSON stored in the changed_data field,
        similar to how Frappe's Version doctype handles its data field.
        """
        try:
            return frappe.parse_json(self.changed_data) if self.changed_data else {}
        except:
            return {}
    
    def get_formatted_data(self):
        """
        User-Friendly Data Formatting: Convert raw audit data to readable format.
        
        Returns:
            dict: Formatted data with human-readable summaries for child table changes
            
        This method processes the raw audit data and creates user-friendly summaries
        for child table operations (like adding roles to users) while preserving
        the original detailed data.
        """
        data = self.get_data()
        if not data:
            return {}
        
        formatted_data = data.copy()
        
        # Format child table additions with user-friendly summaries
        if 'added' in formatted_data and formatted_data['added']:
            formatted_data['added'] = self._format_child_table_data(formatted_data['added'], 'added')
        
        # Format child table removals with user-friendly summaries  
        if 'removed' in formatted_data and formatted_data['removed']:
            formatted_data['removed'] = self._format_child_table_data(formatted_data['removed'], 'removed')
        
        return formatted_data
    
    def _format_child_table_data(self, child_data, action_type):
        """
        Child Table Formatting: Create readable summaries for child table operations.
        
        Args:
            child_data (list): Raw child table data from audit log
            action_type (str): Type of operation ('added' or 'removed')
            
        Returns:
            list: Formatted data with summaries and original data preserved
            
        Processes raw child table data to create human-readable summaries
        while keeping the original detailed data available for inspection.
        """
        formatted_items = []
        
        for item in child_data:
            if len(item) >= 2:
                table_field = item[0]  # Name of the child table field
                table_data = item[1]   # Data that was added/removed
                
                # Generate human-readable summary
                summary = self._get_child_table_summary(table_field, table_data, action_type)
                
                # Preserve original format but add summary
                formatted_items.append([
                    table_field,
                    summary,           # Human-readable summary
                    table_data        # Original detailed data
                ])
        
        return formatted_items
    
    def _get_child_table_summary(self, table_field, table_data, action_type):
        """
        Summary Generation: Create human-readable summaries for specific child table types.
        
        Args:
            table_field (str): Name of the child table field
            table_data (dict): Data that was changed in the child table
            action_type (str): Type of operation performed
            
        Returns:
            str: Human-readable summary of the change
            
        This method contains logic to create meaningful summaries for common
        child table types like roles, permissions, and items.
        """
        if not table_data or not isinstance(table_data, dict):
            return "No data"
        
        # Special handling for user roles
        if table_field == "roles":
            role = table_data.get('role', 'Unknown Role')
            return f"Role: {role}"
        
        # Special handling for user permissions
        elif table_field == "user_permissions":
            doc_type = table_data.get('allow', 'Unknown DocType')
            for_value = table_data.get('for_value', 'Unknown Value')
            return f"Permission: {doc_type} - {for_value}"
        
        # Special handling for item-related tables
        elif "item" in table_field.lower():
            item_code = table_data.get('item_code') or table_data.get('item_name', 'Unknown Item')
            qty = table_data.get('qty', '')
            if qty:
                return f"Item: {item_code} (Qty: {qty})"
            return f"Item: {item_code}"
        
        # Generic handling - try to find the most meaningful field
        display_fields = ['name', 'title', 'subject', 'description', 'item_code', 'role', 'user']
        for field in display_fields:
            if field in table_data and table_data[field]:
                return f"{field.title()}: {table_data[field]}"
        
        # Fallback - show first non-system field with a value
        system_fields = {'doctype', 'name', 'owner', 'creation', 'modified', 
                        'modified_by', 'idx', 'parent', 'parentfield', 'parenttype', '__unsaved'}
        for key, value in table_data.items():
            if key not in system_fields and value:
                return f"{key.replace('_', ' ').title()}: {value}"
        
        return "Child table entry"
    
    @staticmethod
    def clear_old_logs(days: int) -> None:
        """
        Maintenance Function: Delete old audit logs to manage database size.
        
        Args:
            days (int): Number of days of logs to retain (older logs are deleted)
            
        This method uses direct SQL to efficiently delete old audit logs in batches
        to avoid database locks. It bypasses the before_delete hooks to allow
        automated cleanup while preventing manual deletion.
        """
        cutoff = add_to_date(now_datetime(), days=-int(days))

        # Process deletions in batches to avoid long database locks
        BATCH = 5000
        while True:
            # Get batch of old log names
            names = frappe.get_all("Audit Log", 
                                 filters={"timestamp": ["<", cutoff]}, 
                                 pluck="name", 
                                 limit=BATCH)
            if not names:
                break
                
            # Direct SQL delete bypasses before_delete hooks
            frappe.db.sql("""DELETE FROM `tabAudit Log` WHERE name IN %(names)s""", 
                         {"names": tuple(names)})
            frappe.db.commit()


# ---------- PUBLIC API FUNCTIONS ----------

@frappe.whitelist()
def get_audit_log_summary():
    """
    Statistics API: Get summary statistics about audit log activity.
    
    Returns:
        dict: Summary statistics including total logs, recent activity, and action breakdown
        
    This function provides dashboard-ready statistics about audit log activity
    for monitoring and reporting purposes. Requires read permission on Audit Log.
    """
    # Security check
    if not frappe.has_permission("Audit Log", "read"):
        frappe.throw(_("Permission denied."))
    
    # Get total number of audit logs
    total_logs = frappe.db.count("Audit Log")
    
    # Get recent activity count (last 24 hours)
    recent_activity = frappe.db.count("Audit Log", {
        "timestamp": [">=", frappe.utils.add_days(frappe.utils.now_datetime(), -1)]
    })
    
    # Get breakdown of action types in the last 7 days
    action_breakdown = frappe.db.sql("""
        SELECT action_type, COUNT(*) as count
        FROM `tabAudit Log`
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY action_type
        ORDER BY count DESC
    """, as_dict=True)
    
    return {
        "total_logs": total_logs,
        "recent_activity_24h": recent_activity,
        "action_breakdown_7d": action_breakdown
    }

@frappe.whitelist()
def export_audit_logs(filters=None, fields=None):
    """
    Export API: Export audit logs with filtering and field selection.
    
    Args:
        filters (str): JSON string of filters to apply
        fields (str): JSON string of fields to include in export
        
    Returns:
        list: List of audit log records matching the criteria
        
    This function allows authorized users to export audit logs for external
    analysis or compliance reporting. Limited to 10,000 records for performance.
    """
    # Security check
    if not frappe.has_permission("Audit Log", "export"):
        frappe.throw(_("Permission denied."))
    
    # Parse and validate filters
    if filters:
        filters = frappe.parse_json(filters)
    else:
        filters = {}
    
    # Parse and validate field selection
    if fields:
        fields = frappe.parse_json(fields)
    else:
        # Default fields for export
        fields = ["name", "user", "action_type", "reference_doctype", 
                 "reference_name", "ip_address", "timestamp", "changed_data"]
    
    # Fetch audit logs with filters and field selection
    logs = frappe.get_all("Audit Log", 
        filters=filters,
        fields=fields,
        order_by="timestamp DESC",
        limit=10000  # Prevent performance issues with large exports
    )
    
    return logs


# ---------- UTILITY HELPER FUNCTIONS ----------

def _safe_user() -> str:
    """
    User Detection: Safely get the current user.
    
    Returns:
        str: Current user email or "Guest" if unable to determine
        
    This function safely retrieves the current user without throwing errors
    if the session is not available or corrupted.
    """
    try:
        return frappe.session.user or "Guest"
    except Exception:
        return "Guest"

def _parse_ua(ua: str) -> tuple[str, str]:
    """
    User Agent Parsing: Extract browser and OS information from User-Agent string.
    
    Args:
        ua (str): User-Agent string from HTTP request
        
    Returns:
        tuple: (browser_name, operating_system)
        
    This is a lightweight parser that identifies common browsers and operating
    systems without external dependencies. Used for audit trail context.
    """
    if not ua:
        return ("Unknown", "Unknown")

    ua_l = ua.lower()

    # Browser detection logic
    if "edg" in ua_l:
        browser = "Edge"
    elif "chrome" in ua_l and "safari" in ua_l:
        browser = "Chrome"
    elif "safari" in ua_l and "chrome" not in ua_l:
        browser = "Safari"
    elif "firefox" in ua_l:
        browser = "Firefox"
    else:
        # Fallback to first part of User-Agent
        m = re.match(r"^[^/]+", ua)
        browser = m.group(0) if m else "Unknown"

    # Operating system detection logic
    if "windows" in ua_l:
        os = "Windows"
    elif "mac os x" in ua_l or "macintosh" in ua_l:
        os = "macOS"
    elif "android" in ua_l:
        os = "Android"
    elif "iphone" in ua_l or "ipad" in ua_l or "ios" in ua_l:
        os = "iOS"
    elif "linux" in ua_l:
        os = "Linux"
    else:
        os = "Unknown"

    return (browser, os)

def _get_request_info() -> dict:
    """
    Request Context: Extract information about the current HTTP request.
    
    Returns:
        dict: Request information including IP address, browser, and OS
        
    This function gathers context about the current request for audit logging,
    including the user's IP address and browser information.
    """
    ip = "Unknown"
    ua = None
    
    try:
        # Try to get IP from X-Forwarded-For header (proxy/load balancer)
        ip = frappe.get_request_header("X-Forwarded-For")
        if ip and "," in ip:
            # Take first IP if multiple are present
            ip = ip.split(",")[0].strip()
        if not ip:
            # Fallback to direct connection IP
            ip = getattr(frappe.local, "request_ip", "Unknown")
        
        # Get User-Agent string
        ua = frappe.get_request_header("User-Agent")
    except Exception:
        # Gracefully handle cases where request context is not available
        pass
    
    # Parse browser and OS information
    browser, os = _parse_ua(ua or "")
    return {"ip": ip, "browser": browser, "os": os}

def _should_skip(doc=None) -> bool:
    """
    Skip Logic: Determine if a document should be excluded from audit logging.
    
    Args:
        doc: Document object to check
        
    Returns:
        bool: True if the document should be skipped, False otherwise
        
    This function implements the business logic for determining which documents
    should not be audited to prevent noise and infinite loops.
    """
    # Prevent re-entrancy - skip if we're already creating an audit log
    if getattr(frappe.flags, "in_audit_log", False):
        return True

    # Skip during bulk Data Import. Writing a per-row audit record (with a
    # full field diff) for every imported document multiplies the work and is
    # what makes large imports (e.g. 2000 assets) slow enough to time out.
    # The Data Import record itself is the audit trail for the bulk action.
    if getattr(frappe.flags, "in_import", False):
        return True

    # Skip documents of ignored types
    dt = getattr(doc, "doctype", "") if doc else ""
    if dt in IGNORED_DOCTYPES:
        return True
    
    # Skip if Audit Log doctype doesn't exist yet (during installation/migration)
    try:
        if not frappe.db.exists("DocType", "Audit Log"):
            return True
    except Exception:
        return True
    
    return False

def get_diff(old, new, for_child=False, compare_cancelled=False):
    """
    Difference Engine: Calculate differences between two document versions.
    
    Args:
        old: Previous version of the document (can be None for new documents)
        new: Current version of the document
        for_child (bool): Whether this is a child table comparison
        compare_cancelled (bool): Whether to compare cancelled documents
        
    Returns:
        dict: Dictionary containing changes, additions, removals, and row changes
        
    This is the core difference engine that compares two document versions and
    identifies all changes. It matches the implementation used by Frappe's
    Version doctype for consistency.
    """
    if not new:
        return None
    
    # Handle case where old document is None (new document)
    if not old:
        return {
            "new_document": True,
            "created_timestamp": now_datetime(),
            "document_data": new.as_dict() if hasattr(new, 'as_dict') else {}
        }

    # Fields that should not be tracked due to size/performance
    blacklisted_fields = ["Markdown Editor", "Text Editor", "Code", "HTML Editor"]

    # Capture metadata about the change
    data_import = new.flags.via_data_import
    updater_reference = new.flags.updater_reference

    # Initialize result structure
    out = frappe._dict(
        changed=[],      # Field value changes
        added=[],        # Child table rows added
        removed=[],      # Child table rows removed
        row_changed=[],  # Child table rows modified
        data_import=data_import,
        updater_reference=updater_reference,
    )

    # Handle amended documents (documents that replace cancelled ones)
    if not for_child:
        amended_from = new.get("amended_from")
        old_row_name_field = "_amended_from" if (amended_from and amended_from == old.name) else "name"

    # Compare each field in the document
    for df in new.meta.fields:
        # Skip fields that don't store values (except child tables)
        if df.fieldtype in no_value_fields and df.fieldtype not in table_fields:
            continue

        old_value, new_value = old.get(df.fieldname), new.get(df.fieldname)

        # Handle child table fields (one-to-many relationships)
        if not for_child and df.fieldtype in table_fields:
            # Create lookup for old rows by name
            old_rows_by_name = {}
            for d in old_value:
                old_rows_by_name[d.name] = d

            found_rows = set()

            # Check each new row - is it added or modified?
            for i, d in enumerate(new_value):
                old_row_name = getattr(d, old_row_name_field, None)
                
                # Special handling for cancelled document comparison
                if compare_cancelled:
                    if amended_from:
                        if len(old_value) > i:
                            old_row_name = old_value[i].name

                if old_row_name and old_row_name in old_rows_by_name:
                    # Row exists in both versions - check for changes
                    found_rows.add(old_row_name)
                    
                    # Recursively compare child row
                    diff = get_diff(old_rows_by_name[old_row_name], d, for_child=True)
                    if diff and diff.changed:
                        out.row_changed.append((df.fieldname, i, d.name, diff.changed))
                else:
                    # New row added
                    out.added.append([df.fieldname, d.as_dict()])

            # Check for deleted rows
            for d in old_value:
                if d.name not in found_rows:
                    out.removed.append([df.fieldname, d.as_dict()])

        # Handle regular field changes
        elif old_value != new_value:
            if df.fieldtype not in blacklisted_fields:
                # Use formatted values for better display
                old_value = old.get_formatted(df.fieldname) if old_value else old_value
                new_value = new.get_formatted(df.fieldname) if new_value else new_value

            # Record the change if values are still different after formatting
            if old_value != new_value:
                out.changed.append((df.fieldname, old_value, new_value))

    # Check special fields (name and docstatus) for non-child documents
    if not for_child:
        for key in ("name", "docstatus"):
            old_value = getattr(old, key)
            new_value = getattr(new, key)

            if old_value != new_value:
                out.changed.append([key, old_value, new_value])

    # Return differences if any were found
    if any((out.changed, out.added, out.removed, out.row_changed)):
        return out
    else:
        return None

def _create_log(action_type: str, doc=None, changes=None):
    """
    Log Creation Engine: Create and save an audit log entry.
    
    Args:
        action_type (str): Type of action performed (Insert, Update, Delete, etc.)
        doc: Document that was affected
        changes: Dictionary of changes that occurred
        
    This is the core function that creates audit log entries. It gathers all
    necessary context information and safely creates the audit record while
    preventing infinite loops.
    """
    # Prevent re-entrancy loops
    if getattr(frappe.flags, "in_audit_log", False):
        return

    # Normalize unknown action types to prevent errors
    if action_type not in ALLOWED_ACTIONS:
        changes = (changes or {})
        changes["_original_action_type"] = action_type
        action_type = "Update"

    # Set flag to prevent infinite loops
    frappe.flags.in_audit_log = True
    try:
        # Gather request context information
        meta = _get_request_info()
        
        # Build audit log payload
        payload = {
            "doctype": "Audit Log",
            "user": _safe_user(),
            "ip_address": meta["ip"],
            "browser": meta["browser"],
            "os": meta["os"],
            "timestamp": now_datetime(),
            "action_type": action_type,
            "reference_doctype": getattr(doc, "doctype", "") if doc else "",
            "reference_name": getattr(doc, "name", "") if doc else "",
            "changed_data": frappe.as_json(changes or {}, indent=None, separators=(",", ":")),
        }
        
        # Create and save audit log entry
        d = frappe.new_doc("Audit Log")
        d.update(payload)
        
        # Bypass normal validation and permission checks for system-generated audit logs
        d.flags.ignore_permissions = True
        d.flags.ignore_links = True
        d.flags.ignore_mandatory = True
        d.flags.ignore_validate = True
        
        d.insert(ignore_permissions=True, ignore_links=True)
    finally:
        # Always clear the flag to prevent affecting other operations
        frappe.flags.in_audit_log = False


# ---------- DOCUMENT EVENT HANDLERS ----------

def log_create(doc, method=None):
    """
    Document Creation Handler: Log when new documents are created.
    
    Args:
        doc: The document that was created
        method: Hook method name (unused)
        
    This function is called automatically when any document is inserted into
    the system. It captures creation metadata and creates an audit log entry.
    """
    # Check if this document should be skipped
    if _should_skip(doc): 
        return
    
    # Gather creation metadata
    data = {
        "creation": doc.creation,
        "created_by": doc.owner,
        "document_name": doc.name,
        "docstatus": getattr(doc, 'docstatus', 0)
    }
    
    # Add additional metadata for data imports
    if updater_reference := doc.flags.updater_reference:
        data["updater_reference"] = updater_reference
        data["via_data_import"] = True
    
    # Create audit log entry
    _create_log("Insert", doc, data)

def log_update(doc, method=None):
    """
    Document Update Handler: Log when documents are modified.
    
    Args:
        doc: The document that was updated
        method: Hook method name (unused)
        
    This function is called automatically when any document is updated.
    It compares the old and new versions and logs the differences.
    """
    # Check if this document should be skipped
    if _should_skip(doc): 
        return
    
    # Skip update logging for newly created documents to prevent duplicate logs
    # This happens because Frappe often triggers on_update immediately after after_insert
    if doc.is_new():
        return
    
    # Additional check: Skip if an Insert log was created very recently for this document
    # This handles edge cases where is_new() might not catch all scenarios
    from datetime import timedelta
    recent_cutoff = frappe.utils.now_datetime() - timedelta(seconds=5)
    recent_insert = frappe.db.get_value("Audit Log", {
        "reference_doctype": doc.doctype,
        "reference_name": doc.name,
        "action_type": "Insert",
        "timestamp": [">=", recent_cutoff]
    })
    if recent_insert:
        return
    
    # Get the document state before the update
    doc_to_compare = doc.get_doc_before_save()
    
    # Handle amended documents (replacements for cancelled documents)
    if not doc_to_compare and (amended_from := doc.get("amended_from")):
        doc_to_compare = frappe.get_doc(doc.doctype, amended_from)
    
    # Only log if we have a previous version to compare against
    if doc_to_compare:
        # Calculate differences between old and new versions
        diff = get_diff(doc_to_compare, doc)
        if diff:
            # Add impersonation information if available
            if frappe.session:
                if impersonator := frappe.session.data.get("impersonated_by"):
                    diff["impersonated_by"] = impersonator
                if audit_user := frappe.session.data.get("audit_user"):
                    diff["audit_user"] = audit_user
            
            # Create audit log entry
            _create_log("Update", doc, diff)
        else:
            # No changes detected, but still log the update attempt for audit trail
            metadata = {
                "no_changes_detected": True,
                "update_timestamp": now_datetime(),
                "document_status": getattr(doc, 'docstatus', 0)
            }
            _create_log("Update", doc, metadata)
    else:
        # No previous version available (shouldn't happen for updates, but log for debugging)
        metadata = {
            "no_previous_version": True,
            "is_new_document": doc.is_new(),
            "update_timestamp": now_datetime(),
            "document_status": getattr(doc, 'docstatus', 0)
        }
        _create_log("Update", doc, metadata)

def log_delete(doc, method=None):
    """
    Document Deletion Handler: Log when documents are deleted.
    
    Args:
        doc: The document that was deleted
        method: Hook method name (unused)
        
    This function is called automatically when any document is deleted.
    It captures the complete document state before deletion.
    """
    # Check if this document should be skipped
    if _should_skip(doc): 
        return
    
    # Create deletion record with full document snapshot
    diff = {
        "deleted": True,
        "deleted_doc": doc.as_dict(),  # Complete document snapshot
        "deleted_at": now_datetime(),
    }
    
    # Create audit log entry
    _create_log("Delete", doc, diff)