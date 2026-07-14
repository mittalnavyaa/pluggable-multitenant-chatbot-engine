# apps/central-hub-backend/src/telemetry/synthetic/templates.py

from typing import List, Dict, Tuple

# Multilingual greetings and support templates
TRANSLATIONS = {
    "es": {
        "greeting": "Hola, ¿cómo puedo ayudarte hoy?",
        "pricing": "¿Cuánto cuesta el plan premium?",
        "support": "Tengo un problema con mi cuenta, la página está rota.",
        "thanks": "Gracias por la información."
    },
    "fr": {
        "greeting": "Bonjour, comment puis-je vous aider aujourd'hui?",
        "pricing": "Combien coûte le forfait premium?",
        "support": "J'ai un problème avec mon compte, la page est cassée.",
        "thanks": "Merci pour les informations."
    },
    "hi": {
        "greeting": "नमस्ते, मैं आज आपकी क्या सहायता कर सकता हूँ?",
        "pricing": "प्रीमियम प्लान की कीमत कितनी है?",
        "support": "मुझे मेरे खाते में एक समस्या आ रही है, पेज लोड नहीं हो रहा है।",
        "thanks": "जानकारी के लिए धन्यवाद।"
    }
}

# Dialog templates mapped by (tenant_id, intent_category)
# Format of dialog: list of turns (role, message)
DIALOG_TEMPLATES: Dict[str, Dict[str, List[List[Tuple[str, str]]]]] = {
    "tensor": {
        "Course Inquiry": [
            [
                ("user", "What machine learning courses do you recommend for learning PyTorch deep learning?"),
                ("assistant", "I highly recommend our 'Deep Learning with PyTorch' specialization. It covers neural networks, optimization algorithms, and transformer models with hands-on labs.")
            ]
        ],
        "Admissions": [
            [
                ("user", "When are applications due for the advanced data science bootcamp?"),
                ("assistant", "Applications for the next cohort close on August 1st. Make sure to upload your resume and complete the python coding assessment before the deadline.")
            ]
        ],
        "Pricing": [
            [
                ("user", "How much does the developer license for Tensor AI cost?"),
                ("assistant", "The Tensor AI Developer license starts at $29/month per developer, billed annually. This includes 50,000 API requests and standard email support."),
                ("user", "Do you have volume licensing?"),
                ("assistant", "Yes, we offer enterprise volume discounts for teams larger than 10 developers. Please contact our sales team to request a customized quote.")
            ],
            [
                ("user", "Can you show me the pricing options for the GPU compute clusters?"),
                ("assistant", "Our GPU clusters start at $0.90/hour for NVIDIA T4 instances, and up to $3.50/hour for A100 instances. Spot instance pricing is also available.")
            ]
        ],
        "Registration": [
            [
                ("user", "How do I register my API client credentials in the Tensor console?"),
                ("assistant", "Log into the Tensor Console, navigate to Developer Settings -> API Keys, and click 'Create New Client'. Make sure to save the secret token securely.")
            ]
        ],
        "Billing": [
            [
                ("user", "My credit card was declined for the cloud cluster subscription. Can I pay via PayPal?"),
                ("assistant", "Currently we only accept major credit cards and ACH bank transfers. You can update your payment method under the Billing settings tab in your profile.")
            ]
        ],
        "Technical Support": [
            [
                ("user", "I am getting a Cuda Out Of Memory exception when training my ResNet-50 model on my local setup. How can I resolve this?"),
                ("assistant", "To fix CUDA out of memory errors, try: 1) reducing the training batch size, 2) using mixed precision training via torch.cuda.amp, or 3) clearing the PyTorch cache using torch.cuda.empty_cache() between epochs.")
            ],
            [
                ("user", "Why does my vector index update take so long on the Qdrant database collection?"),
                ("assistant", "Vector indexing latency is usually caused by heavy indexing during insertions. You can temporarily disable indexes during upload or increase Qdrant's indexing thread pool size.")
            ]
        ],
        "Product Information": [
            [
                ("user", "Does Tensor AI support on-premise deployments, or is it cloud-only?"),
                ("assistant", "Tensor AI fully supports on-premise deployments via Helm charts on Kubernetes, as well as managed cloud deployments on AWS, GCP, and Azure.")
            ]
        ],
        "Documentation": [
            [
                ("user", "Where can I find the API reference for the python SDK client?"),
                ("assistant", "You can access the full Python SDK client reference at developer.tensor-ai.envoy.com/docs/sdk/python. It includes quickstarts and class docs.")
            ]
        ],
        "Feature Request": [
            [
                ("user", "I would like to request support for fine-tuning llama-3 models directly from the UI dashboard."),
                ("assistant", "Thank you for the suggestion! Fine-tuning custom models is on our Q4 roadmap. I have logged this request with the product management team.")
            ]
        ],
        "Bug Report": [
            [
                ("user", "The export dataset endpoint is returning a 500 internal server error when handling null timestamps."),
                ("assistant", "That sounds like a bug. I have opened ticket TENSOR-892 for the engineering team. We will check the timestamp parsing logic on the export router.")
            ]
        ],
        "Complaint": [
            [
                ("user", "Your model hosting API service is extremely slow and has been down twice this week!"),
                ("assistant", "I sincerely apologize for the disruptions. We experienced a temporary network outage in our us-east cluster. We are adding redundant nodes to improve stability.")
            ]
        ],
        "Feedback": [
            [
                ("user", "The new dashboard latency charts are extremely helpful and easy to read. Nice job!"),
                ("assistant", "Thank you so much! We are glad you find the analytics charts helpful. We are continuously working to make dashboard indicators more powerful.")
            ]
        ],
        "Sales Inquiry": [
            [
                ("user", "We are a large enterprise looking to deploy Tensor AI across 500 team members. Can we get an enterprise demo?"),
                ("assistant", "Yes, absolutely! We offer customized demos and pilot programs for enterprise teams. A sales representative will contact you shortly to schedule a session.")
            ]
        ],
        "Enterprise Inquiry": [
            [
                ("user", "What are the SLA terms and support packages available for enterprise deployments?"),
                ("assistant", "Our Enterprise SLA guarantees 99.9% uptime, 24/7 dedicated support engineer access, and sub-hour response times for critical system issues.")
            ]
        ],
        "General Information": [
            [
                ("user", "What is the core technology behind the chatbot routing engine?"),
                ("assistant", "Our routing engine uses semantic search embeddings to classify user inputs and match them to the relevant knowledge bases or transactional intent agents.")
            ]
        ],
        "Other": [
            [
                ("user", "Can you explain the difference between supervised and unsupervised learning?"),
                ("assistant", "Supervised learning uses labeled dataset examples to train algorithms, while unsupervised learning discovers hidden patterns in unlabeled data.")
            ]
        ]
    },
    "admissions": {
        "Course Inquiry": [
            [
                ("user", "What subjects are covered in the introduction to programming course?"),
                ("assistant", "The course covers Python basics, variables, conditional statements, loops, lists, dictionary data structures, and writing functions.")
            ]
        ],
        "Admissions": [
            [
                ("user", "What documents are required to apply for the undergraduate admissions?"),
                ("assistant", "You need to submit: 1) high school transcripts, 2) copy of your government ID, 3) letter of recommendation, and 4) a personal statement essay.")
            ],
            [
                ("user", "Can I check my current application status? My registration ID is ADM-89231."),
                ("assistant", "Let me check ADM-89231. Your application is currently 'Under Review' by the admissions committee. You should receive a final response within two weeks.")
            ]
        ],
        "Pricing": [
            [
                ("user", "What is the fee per semester for the Computer Science degree program?"),
                ("assistant", "The tuition fee for Computer Science is $4,500 per semester for in-state students and $9,200 per semester for out-of-state/international students.")
            ]
        ],
        "Registration": [
            [
                ("user", "How do I register for classes if I'm a new transfer student?"),
                ("assistant", "Transfer students can register for classes online via the Student Portal after their credit evaluation is completed by the registrar's office.")
            ]
        ],
        "Billing": [
            [
                ("user", "Is there a payment plan option for paying tuition fees, or do I have to pay all at once?"),
                ("assistant", "Yes, we offer an installment payment plan. You can split the tuition into three equal payments spread across the academic semester.")
            ]
        ],
        "Technical Support": [
            [
                ("user", "I am locked out of my admissions application portal account. Can you help?"),
                ("assistant", "To reset your password and unlock your account, click the 'Forgot Password' link on the login page, or contact admissions-support@envoy-ai.com.")
            ]
        ],
        "Product Information": [
            [
                ("user", "Is this admissions helper an AI assistant, or a live support person?"),
                ("assistant", "I am the Admissions Portal AI Virtual Assistant. I am online 24/7 to answer application, tuition, and registration questions.")
            ]
        ],
        "Documentation": [
            [
                ("user", "Where is the student handbook PDF file located?"),
                ("assistant", "You can download the official Student Code of Conduct and General Handbook from admissions.envoy-ai.com/resources/handbook.pdf.")
            ]
        ],
        "Feature Request": [
            [
                ("user", "Can you add a way to upload documents directly inside the chatbot window?"),
                ("assistant", "Thank you for the request! While you cannot upload files directly inside this chat window, you can upload them securely in your application portal account.")
            ]
        ],
        "Bug Report": [
            [
                ("user", "The upload button on the documents submission tab keeps spin-locking on Safari browser."),
                ("assistant", "Thank you for reporting. This is a known browser compatibility issue on some Safari builds. Please try uploading using Chrome or Firefox.")
            ]
        ],
        "Complaint": [
            [
                ("user", "I submitted my documents three weeks ago and nobody has updated my application status! This is frustrating."),
                ("assistant", "I understand your frustration and apologize for the delay. We have a high volume of applications. I will flag your case ID to the admissions office.")
            ]
        ],
        "Feedback": [
            [
                ("user", "Your system helped me find the scholarship page in under 10 seconds. Thank you!"),
                ("assistant", "You are very welcome! We are thrilled to hear that you found the information quickly. Best of luck with your application!")
            ]
        ],
        "Sales Inquiry": [
            [
                ("user", "Do you offer group discounts for corporate enrollment in the data analytics certificates?"),
                ("assistant", "Yes! For cohorts of 10 or more corporate enrollments, we offer custom pricing models and customized training plans. Contact admissions-sales@envoy-ai.com.")
            ]
        ],
        "Enterprise Inquiry": [
            [
                ("user", "Who is the head of corporate partnerships for bulk admissions programs?"),
                ("assistant", "Our corporate partnerships department is led by Sarah Jenkins. You can reach out directly at partnerships@envoy-ai.com.")
            ]
        ],
        "General Information": [
            [
                ("user", "Are the campus hostel rooms fully furnished, and do they include Wi-Fi?"),
                ("assistant", "Yes, all campus hostel rooms are fully furnished with a bed, desk, chair, and wardrobe. High-speed Wi-Fi and weekly laundry services are included.")
            ]
        ],
        "Other": [
            [
                ("user", "What is the weather like in Boston during the autumn semester?"),
                ("assistant", "Boston autumns are beautiful but cool, with temperatures ranging from 45°F to 65°F (7°C to 18°C). We recommend bringing layered clothing.")
            ]
        ]
    },
    "internal-support": {
        "Technical Support": [
            [
                ("user", "How do I connect my company laptop to the secure VPN from home?"),
                ("assistant", "To connect to the VPN: 1) Open Cisco AnyConnect, 2) Select server 'vpn.envoy-ai.com', 3) Enter corporate SSO credentials and verify via Okta MFA.")
            ],
            [
                ("user", "My laptop screen is flickering, and I cannot see anything. Can I get a replacement?"),
                ("assistant", "Please bring the laptop to the IT help desk in Room 402 for hardware inspection. If it is damaged, we will issue a replacement laptop immediately.")
            ]
        ],
        "Registration": [
            [
                ("user", "How do I request access to the production AWS console environment?"),
                ("assistant", "AWS production console access must be requested through our internal IAM portal. It requires manager approval and active security training completion.")
            ]
        ],
        "General Information": [
            [
                ("user", "What are the IT help desk operating hours?"),
                ("assistant", "The IT Help Desk is open Monday to Friday, from 8:00 AM to 6:00 PM EST. For emergency outages, you can reach the on-call engineer at extension 9111.")
            ]
        ]
    },
    "hr-portal": {
        "Course Inquiry": [
            [
                ("user", "Does the company offer training courses and learning reimbursements?"),
                ("assistant", "Yes, we reimburse up to $3,000 annually for approved certification courses and learning resources. You can apply via the HR Portal -> Learning tab.")
            ]
        ],
        "Admissions": [
            [
                ("user", "How do I add my dependents to my employee healthcare insurance program?"),
                ("assistant", "Dependents can be added during open enrollment, or within 30 days of a qualifying life event (like marriage or birth) under the Benefits section.")
            ]
        ],
        "Technical Support": [
            [
                ("user", "I cannot log my hours on the Workday timesheet site. It says my account is suspended."),
                ("assistant", "Account suspensions on Workday are usually handled by the payroll team. I will open a ticket to investigate if your contract profile is complete.")
            ]
        ]
    },
    "placement-cell": {
        "Course Inquiry": [
            [
                ("user", "Are there resume review workshops before the campus interviews start?"),
                ("assistant", "Yes, the Placement Cell hosts resume review workshops every Tuesday and Thursday. Check the calendar in the placement dashboard to sign up.")
            ]
        ],
        "Admissions": [
            [
                ("user", "What is the minimum grade eligibility criteria for the top tech companies visiting campus?"),
                ("assistant", "Most visiting technology companies require a minimum CGPA of 7.5 or above with no active backlogs to qualify for recruitment drives.")
            ]
        ],
        "General Information": [
            [
                ("user", "Which companies are visiting campus next week for the engineering placements?"),
                ("assistant", "Next week we are hosting Google, Microsoft, and Uber. You can view placement schedules and register for slots on the Placement Portal.")
            ]
        ]
    },
    "website-analyzer": {
        "Technical Support": [
            [
                ("user", "Why is my website loading speed so slow on mobile devices according to the analyzer audit?"),
                ("assistant", "Mobile loading latency is typically caused by uncompressed images, unused JavaScript, and slow server response times. Try optimizing assets and using a CDN.")
            ]
        ],
        "Documentation": [
            [
                ("user", "Where can I find instructions on how to set up the analyzer tracking pixel?"),
                ("assistant", "The setup documentation is available at docs.website-analyzer.envoy.com/pixel-installation. Just copy-paste the snippet into your HTML head.")
            ]
        ]
    },
    "knowledge-base": {
        "General Information": [
            [
                ("user", "What is the company policy on remote work and hybrid working hours?"),
                ("assistant", "Our hybrid policy requires employees to spend at least 2 days a week in their local office. Core collaborative hours are between 10:00 AM and 4:00 PM.")
            ]
        ],
        "Documentation": [
            [
                ("user", "Where is the business continuity policy folder?"),
                ("assistant", "The Business Continuity and Disaster Recovery plan documents are stored in the secure Sharepoint drive under Corporate Policies -> Business Continuity.")
            ]
        ]
    }
}

# General templates used to generate standard intents if a specific tenant template is missing
DEFAULT_DIALOGS: Dict[str, List[List[Tuple[str, str]]]] = {
    "Course Inquiry": [
        [
            ("user", "Can you tell me about the available courses and certificates?"),
            ("assistant", "We offer multiple certification tracks in technology, business analytics, and project management. Each track takes 3-6 months to complete.")
        ]
    ],
    "Admissions": [
        [
            ("user", "What is the process for submitting an application?"),
            ("assistant", "Fill out the online application form, upload your academic certificates, pay the processing fee, and click submit. You will receive an email confirmation.")
        ]
    ],
    "Pricing": [
        [
            ("user", "What is the cost of the subscription plans?"),
            ("assistant", "Our plans start at $19/month for the starter tier, $49/month for the professional tier, and customized pricing for enterprise customers.")
        ]
    ],
    "Registration": [
        [
            ("user", "How do I create a new user account?"),
            ("assistant", "Click the 'Sign Up' button in the upper right corner, enter your email, create a password, and verify your account via the activation link sent to your inbox.")
        ]
    ],
    "Billing": [
        [
            ("user", "I want to cancel my auto-renewal. How do I do that?"),
            ("assistant", "Go to your Account Settings -> Billing & Subscription, and toggle off the auto-renewal option. You will retain access until the end of the current billing cycle.")
        ]
    ],
    "Technical Support": [
        [
            ("user", "The website is failing to load my profile dashboard. It keeps throwing a network error."),
            ("assistant", "Please clear your browser cookies and cache, or try logging in from an incognito window. If the issue persists, contact support@envoy-ai.com.")
        ]
    ],
    "Product Information": [
        [
            ("user", "What features are included in the latest product release version?"),
            ("assistant", "The latest version introduces multi-tenant pipeline metrics, custom styling configurations, intent taxonomy checks, and automated WebSocket rollups.")
        ]
    ],
    "Documentation": [
        [
            ("user", "Where can I download the documentation user guides?"),
            ("assistant", "All user guides and developer API reference manuals are located in the resource portal under documentation.envoy-ai.com.")
        ]
    ],
    "Feature Request": [
        [
            ("user", "Can we get support for exports in Excel format instead of just CSV?"),
            ("assistant", "Excel export is a highly requested feature! I have registered this ticket with the development team, and we plan to deploy it in our next minor release.")
        ]
    ],
    "Bug Report": [
        [
            ("user", "The character counter on the search bar is off by one letter when typing spaces."),
            ("assistant", "Thank you for the detailed feedback. This character count boundary error has been logged, and we will deploy a patch fix this afternoon.")
        ]
    ],
    "Complaint": [
        [
            ("user", "I've been waiting for my password reset email for 4 hours and it still hasn't arrived!"),
            ("assistant", "I understand your frustration. Please check your Spam folder. I will also notify our system administrator to verify if the SMTP server is active.")
        ]
    ],
    "Feedback": [
        [
            ("user", "The interface feels extremely premium and fast. I love the new dark mode theme!"),
            ("assistant", "We appreciate the feedback! The dark theme config was customized to give the console UI a modern, high-contrast look.")
        ]
    ],
    "Sales Inquiry": [
        [
            ("user", "I would like to purchase 50 seats for my team. Can I get a sales quote?"),
            ("assistant", "Certainly! I will connect you with a sales representative to prepare a formal proposal. Please provide your business email and contact number.")
        ]
    ],
    "Enterprise Inquiry": [
        [
            ("user", "Do you comply with SOC 2 security compliance guidelines for enterprise data storage?"),
            ("assistant", "Yes, our cloud systems are fully SOC 2 Type II certified. We apply TLS 1.3 encryption in transit and AES-256 encryption at rest for all tenants.")
        ]
    ],
    "General Information": [
        [
            ("user", "What are your customer support working hours?"),
            ("assistant", "Our support agents are available online Monday through Friday, 9:00 AM to 8:00 PM EST. Offline queries are handled via email support.")
        ]
    ],
    "Other": [
        [
            ("user", "Can you help me write an email template to my professor?"),
            ("assistant", "Sure! Here is a simple draft: 'Dear Professor, I hope this email finds you well. I would like to schedule a quick meeting to discuss my term paper. Thank you.'")
        ]
    ]
}

# Error scenario templates (generating issues in Gateway or ChatMessage logs)
ERROR_SCENARIOS = [
    {
        "status": "TIMEOUT",
        "error_reason": "API service connection timeout after 5000ms",
        "payload": {
            "query": "Generate a summary report of my data cluster logs",
            "assistant_response": "Error: Request timeout. The model server failed to respond in time."
        }
    },
    {
        "status": "VALIDATION_FAILURE",
        "error_reason": "Missing required runtime identifier: bot_id.",
        "payload": {
            "query": "Is the admissions office open today?",
            "assistant_response": "Error: Validation failure. Missing runtime parameters."
        }
    },
    {
        "status": "RATE_LIMITED",
        "error_reason": "Rate limit exceeded. Client has made more than 60 requests/min",
        "payload": {
            "query": "tell me about billing plans",
            "assistant_response": "Error 429: Too many requests. Please wait a minute before retrying."
        }
    },
    {
        "status": "AUTH_FAILURE",
        "error_reason": "Missing or invalid Bearer Token",
        "payload": {
            "query": "test auth connection",
            "assistant_response": "Error 401: Unauthorized access token."
        }
    },
    {
        "status": "INTERNAL_ERROR",
        "error_reason": "NullPointerException: database link failed",
        "payload": {
            "query": "who is my advisor?",
            "assistant_response": "Error 500: An unexpected internal error occurred on the database engine."
        }
    }
]

def get_dialog(tenant_id: str, intent: str, random_obj) -> List[Tuple[str, str]]:
    """Helper function to fetch or fall back to a dialog flow based on tenant and intent."""
    tenant_dict = DIALOG_TEMPLATES.get(tenant_id, {})
    options = tenant_dict.get(intent)
    
    if not options:
        # Fall back to default dialog templates
        options = DEFAULT_DIALOGS.get(intent)
        
    if not options:
        # Final fallback
        options = [[("user", f"Inquiry about {intent}"), ("assistant", f"I can assist you with your inquiry regarding {intent}.")]]
        
    # Return a random pick from the options list using the seeded random object
    return random_obj.choice(options)
