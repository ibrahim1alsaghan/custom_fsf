import frappe

def execute():
    """Create print format for Client Evaluation Form"""
    
    # Check if print format already exists
    if frappe.db.exists("Print Format", "Client Evaluation Form - Detail"):
        print("Client Evaluation Form print format already exists")
        return
    
    # Create the print format
    print_format = frappe.get_doc({
        "doctype": "Print Format",
        "name": "Client Evaluation Form - Detail",
        "doc_type": "Client Evaluation Form",
        "module": "custom fsf",
        "standard": "No",
        "raw_printing": 0,
        "html": """
<div class="print-format">
    <div class="print-heading">
        <h1>Client Evaluation Form</h1>
    </div>
    
    <div class="print-format-content">
        <div class="row">
            <div class="col-6">
                <p><strong>Project:</strong> {{ doc.project }}</p>
                <p><strong>Client:</strong> {{ doc.client }}</p>
            </div>
            <div class="col-6">
                <p><strong>Evaluation Date:</strong> {{ doc.evaluation_date }}</p>
            </div>
        </div>
        
        <hr>
        
        <h3>Performance Evaluation</h3>
        <table class="table table-bordered">
            <tr>
                <td><strong>Responsiveness & Communication:</strong></td>
                <td>{{ doc.responsiveness_communication }}</td>
            </tr>
            <tr>
                <td><strong>Clarity of Requirements:</strong></td>
                <td>{{ doc.clarity_requirements }}</td>
            </tr>
            <tr>
                <td><strong>Timeliness of Approvals & Feedback:</strong></td>
                <td>{{ doc.timeliness_approvals }}</td>
            </tr>
            <tr>
                <td><strong>Cooperation & Engagement:</strong></td>
                <td>{{ doc.cooperation_engagement }}</td>
            </tr>
            <tr style="background-color: #f8f9fa; font-weight: bold;">
                <td><strong>Overall Satisfaction Rating:</strong></td>
                <td>{{ doc.overall_satisfaction }}</td>
            </tr>
        </table>
        
        {% if doc.evaluation_comments %}
        <h3>Evaluation Comments</h3>
        <div class="well">
            {{ doc.evaluation_comments }}
        </div>
        {% endif %}
        
        {% if doc.recommendations %}
        <h3>Recommendations</h3>
        <div class="well">
            {{ doc.recommendations }}
        </div>
        {% endif %}
    </div>
</div>
        """,
        "css": """
.print-format {
    font-family: Arial, sans-serif;
    line-height: 1.6;
}

.print-heading {
    text-align: center;
    margin-bottom: 30px;
    border-bottom: 2px solid #333;
    padding-bottom: 10px;
}

.print-heading h1 {
    color: #333;
    margin: 0;
}

.table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

.table td {
    padding: 10px;
    border: 1px solid #ddd;
}

.table tr:nth-child(even) {
    background-color: #f9f9f9;
}

.well {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 15px;
    margin: 10px 0;
}

h3 {
    color: #333;
    border-bottom: 1px solid #ddd;
    padding-bottom: 5px;
    margin-top: 30px;
}

hr {
    margin: 20px 0;
    border: 0;
    border-top: 1px solid #ddd;
}
        """
    })
    
    print_format.insert()
    frappe.db.commit()
    
    print("Created Client Evaluation Form print format")
