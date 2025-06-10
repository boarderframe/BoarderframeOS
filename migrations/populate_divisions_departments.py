#!/usr/bin/env python3
"""
Populate Divisions & Departments Script
Populates the new organizational structure with the finalized divisions, departments, and leaders
"""

import asyncio
import asyncpg
import logging
from datetime import datetime
from typing import Dict, List, Any
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrganizationalPopulator:
    def __init__(self, db_url: str = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos"):
        self.db_url = db_url
        self.conn = None
        
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = await asyncpg.connect(self.db_url)
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
    
    async def clear_existing_organizational_data(self):
        """Clear existing organizational data for clean population"""
        logger.info("Clearing existing organizational data...")
        
        # Delete in correct order due to foreign key constraints
        tables = [
            'strategic_objectives',
            'department_collaborations',
            'department_capabilities',
            'leadership_succession',
            'organizational_hierarchy',
            'division_leadership',
            'department_performance',  # renamed from department_status
            'agent_department_assignments',
            'department_assignment_history',
            'department_native_agents',
            'department_leaders',
            'departments',  # Keep existing departments, just update them
            'divisions'
        ]
        
        for table in tables:
            if table != 'departments':  # Don't clear departments, we'll update them
                await self.conn.execute(f"DELETE FROM {table}")
                logger.info(f"Cleared {table}")
        
        logger.info("Organizational data cleared")
    
    async def populate_divisions(self) -> Dict[str, int]:
        """Populate the 9 divisions"""
        logger.info("Populating divisions...")
        
        divisions_data = [
            {
                'key': 'executive',
                'name': 'Executive Division',
                'description': 'Strategic leadership and agent lifecycle management',
                'purpose': 'Supreme strategic direction, agent development, and organizational coordination',
                'priority': 1
            },
            {
                'key': 'programming_development',
                'name': 'Programming & Development Division',
                'description': 'All programming activities - core system and commercial products',
                'purpose': 'Software creation, system programming, and quality assurance',
                'priority': 2
            },
            {
                'key': 'information_technology',
                'name': 'Information Technology Division',
                'description': 'Technical infrastructure, data systems, and operations',
                'purpose': 'Infrastructure management, security, data systems, and analytics',
                'priority': 3
            },
            {
                'key': 'product_operations',
                'name': 'Product Operations Division',
                'description': 'Customer-facing products, services, and technical delivery',
                'purpose': 'Platform services, deployment, product management, and API integration',
                'priority': 4
            },
            {
                'key': 'revenue_generation',
                'name': 'Revenue Generation Division',
                'description': 'Direct revenue creation and optimization',
                'purpose': 'Sales, marketing, and revenue operations',
                'priority': 5
            },
            {
                'key': 'business_operations',
                'name': 'Business Operations Division',
                'description': 'Internal business functions and organizational development',
                'purpose': 'Finance, legal, HR, procurement, and organizational learning',
                'priority': 6
            },
            {
                'key': 'customer_experience',
                'name': 'Customer Experience Division',
                'description': 'Complete customer lifecycle and satisfaction',
                'purpose': 'Customer success, support, experience design, and account management',
                'priority': 7
            },
            {
                'key': 'content_generation',
                'name': 'Content Generation Division',
                'description': 'Creative content and media production',
                'purpose': 'Creative services, content strategy, and media production',
                'priority': 8
            },
            {
                'key': 'continuous_improvement',
                'name': 'Continuous Improvement Division',
                'description': 'Innovation, research, and organizational advancement',
                'purpose': 'Innovation, research & development, and strategic advancement',
                'priority': 9
            }
        ]
        
        division_id_map = {}
        
        for division in divisions_data:
            div_id = await self.conn.fetchval("""
                INSERT INTO divisions (
                    division_key, division_name, division_description, 
                    division_purpose, priority, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, division['key'], division['name'], division['description'],
                division['purpose'], division['priority'], True)
            
            division_id_map[division['key']] = div_id
            logger.info(f"  Created division: {division['name']} (ID: {div_id})")
        
        logger.info(f"Populated {len(divisions_data)} divisions")
        return division_id_map
    
    async def populate_departments(self, division_id_map: Dict[str, int]) -> Dict[str, str]:
        """Populate the 28 departments within divisions"""
        logger.info("Populating departments...")
        
        departments_data = [
            # Executive Division
            {
                'key': 'executive_leadership',
                'name': 'Executive Leadership',
                'division': 'executive',
                'description': 'Strategic Command Center',
                'purpose': 'Supreme strategic direction and executive leadership',
                'category': 'Executive',
                'priority': 1,
                'agent_capacity': 15
            },
            {
                'key': 'strategic_planning',
                'name': 'Strategic Planning',
                'division': 'executive',
                'description': 'Future Architecture & Vision Mastery',
                'purpose': 'Long-term strategic planning, vision architecture, and business development',
                'category': 'Executive',
                'priority': 2,
                'agent_capacity': 10
            },
            {
                'key': 'coordination_orchestration',
                'name': 'Coordination & Orchestration',
                'division': 'executive',
                'description': 'Multi-Department Command Center',
                'purpose': 'Multi-department coordination, workflow orchestration, and complex business processes',
                'category': 'Executive',
                'priority': 3,
                'agent_capacity': 12
            },
            {
                'key': 'agent_development',
                'name': 'Agent Development',
                'division': 'executive',
                'description': 'Creation & Evolution Center',
                'purpose': 'Agent lifecycle management, digital DNA creation, and team evolution',
                'category': 'Executive',
                'priority': 4,
                'agent_capacity': 20
            },
            
            # Programming & Development Division
            {
                'key': 'core_systems_programming',
                'name': 'Core Systems Programming',
                'division': 'programming_development',
                'description': 'Core System Development',
                'purpose': 'BoarderframeOS platform development, system programming, core infrastructure code',
                'category': 'Programming',
                'priority': 1,
                'agent_capacity': 25
            },
            {
                'key': 'software_factory',
                'name': 'Software Factory',
                'division': 'programming_development',
                'description': 'Commercial Product Creation',
                'purpose': 'Commercial application development, product creation, continuous software delivery',
                'category': 'Programming',
                'priority': 2,
                'agent_capacity': 30
            },
            {
                'key': 'quality_assurance',
                'name': 'Quality Assurance',
                'division': 'programming_development',
                'description': 'Quality & Testing Excellence',
                'purpose': 'Software testing, agent quality validation, performance testing, and reliability assurance',
                'category': 'Programming',
                'priority': 3,
                'agent_capacity': 15
            },
            
            # Information Technology Division
            {
                'key': 'infrastructure_operations',
                'name': 'Infrastructure & Operations',
                'division': 'information_technology',
                'description': 'Technical Infrastructure & Operations',
                'purpose': 'MCP servers, system connectivity, infrastructure monitoring, and technical operations',
                'category': 'Infrastructure',
                'priority': 1,
                'agent_capacity': 20
            },
            {
                'key': 'security',
                'name': 'Security',
                'division': 'information_technology',
                'description': 'Defense & Protection Mastery',
                'purpose': 'Cybersecurity, data protection, threat elimination, and compliance management',
                'category': 'Infrastructure',
                'priority': 2,
                'agent_capacity': 15
            },
            {
                'key': 'data_management',
                'name': 'Data Management',
                'division': 'information_technology',
                'description': 'Data Sanctuaries & Knowledge Architecture',
                'purpose': 'Database management, knowledge curation, agent memory preservation, and information architecture',
                'category': 'Infrastructure',
                'priority': 3,
                'agent_capacity': 18
            },
            {
                'key': 'analytics_monitoring',
                'name': 'Analytics & Monitoring',
                'division': 'information_technology',
                'description': 'Data Intelligence & System Monitoring',
                'purpose': 'Data analysis, business intelligence, system monitoring, and performance metrics',
                'category': 'Infrastructure',
                'priority': 4,
                'agent_capacity': 12
            },
            
            # Product Operations Division
            {
                'key': 'platform_services',
                'name': 'Platform Services',
                'division': 'product_operations',
                'description': 'Customer-Facing Excellence',
                'purpose': 'API hosting, live service delivery, and production system management',
                'category': 'Product',
                'priority': 1,
                'agent_capacity': 20
            },
            {
                'key': 'devops_deployment',
                'name': 'DevOps & Deployment',
                'division': 'product_operations',
                'description': 'Deployment & System Reliability',
                'purpose': 'CI/CD pipelines, production deployments, system reliability, and incident response',
                'category': 'Product',
                'priority': 2,
                'agent_capacity': 15
            },
            {
                'key': 'product_management',
                'name': 'Product Management',
                'division': 'product_operations',
                'description': 'Product Strategy & Development',
                'purpose': 'Product roadmap, feature development, and customer-facing product strategy',
                'category': 'Product',
                'priority': 3,
                'agent_capacity': 10
            },
            {
                'key': 'api_gateway_integration',
                'name': 'API Gateway & Integration',
                'division': 'product_operations',
                'description': 'Integration & API Management',
                'purpose': 'API management, external integrations, rate limiting, and partnership APIs',
                'category': 'Product',
                'priority': 4,
                'agent_capacity': 12
            },
            
            # Revenue Generation Division
            {
                'key': 'sales',
                'name': 'Sales',
                'division': 'revenue_generation',
                'description': 'Revenue Generation & Territory Expansion',
                'purpose': 'Customer acquisition, deal closing, and territory expansion',
                'category': 'Revenue',
                'priority': 1,
                'agent_capacity': 20
            },
            {
                'key': 'marketing',
                'name': 'Marketing',
                'division': 'revenue_generation',
                'description': 'Brand Evangelism & Message Amplification',
                'purpose': 'Brand evangelism, content strategy, and market expansion',
                'category': 'Revenue',
                'priority': 2,
                'agent_capacity': 18
            },
            {
                'key': 'revenue_operations',
                'name': 'Revenue Operations',
                'division': 'revenue_generation',
                'description': 'Revenue Optimization & Operations',
                'purpose': 'Billing systems, subscription management, revenue analytics, and pricing optimization',
                'category': 'Revenue',
                'priority': 3,
                'agent_capacity': 12
            },
            
            # Business Operations Division
            {
                'key': 'finance',
                'name': 'Finance',
                'division': 'business_operations',
                'description': 'Treasury & Wealth Multiplication',
                'purpose': 'Financial management, cost optimization, and wealth accumulation',
                'category': 'Business',
                'priority': 1,
                'agent_capacity': 15
            },
            {
                'key': 'legal_compliance',
                'name': 'Legal & Compliance',
                'division': 'business_operations',
                'description': 'Justice & Protection',
                'purpose': 'Legal compliance, contract management, risk mitigation, and regulatory governance',
                'category': 'Business',
                'priority': 2,
                'agent_capacity': 10
            },
            {
                'key': 'human_resources',
                'name': 'Human Resources',
                'division': 'business_operations',
                'description': 'Agent Development & Culture',
                'purpose': 'Agent development, culture building, and organizational excellence',
                'category': 'Business',
                'priority': 3,
                'agent_capacity': 12
            },
            {
                'key': 'procurement_partnerships',
                'name': 'Procurement & Partnerships',
                'division': 'business_operations',
                'description': 'Resource Acquisition & Strategic Partnerships',
                'purpose': 'Vendor management, strategic partnerships, and external resource acquisition',
                'category': 'Business',
                'priority': 4,
                'agent_capacity': 8
            },
            {
                'key': 'learning_development',
                'name': 'Learning & Development',
                'division': 'business_operations',
                'description': 'Knowledge Transfer & Education',
                'purpose': 'Training programs, knowledge transfer, and organizational learning',
                'category': 'Business',
                'priority': 5,
                'agent_capacity': 10
            },
            
            # Customer Experience Division
            {
                'key': 'customer_success',
                'name': 'Customer Success',
                'division': 'customer_experience',
                'description': 'Customer Success & Satisfaction',
                'purpose': 'Customer onboarding, relationship management, and success coaching',
                'category': 'Customer',
                'priority': 1,
                'agent_capacity': 15
            },
            {
                'key': 'customer_support',
                'name': 'Customer Support',
                'division': 'customer_experience',
                'description': 'Customer Assistance & Issue Resolution',
                'purpose': 'Issue resolution, help desk operations, and customer assistance',
                'category': 'Customer',
                'priority': 2,
                'agent_capacity': 20
            },
            {
                'key': 'customer_experience_design',
                'name': 'Customer Experience Design',
                'division': 'customer_experience',
                'description': 'Experience Design & Optimization',
                'purpose': 'Customer journey optimization, satisfaction measurement, and experience design',
                'category': 'Customer',
                'priority': 3,
                'agent_capacity': 8
            },
            {
                'key': 'customer_retention',
                'name': 'Customer Retention',
                'division': 'customer_experience',
                'description': 'Retention & Loyalty Management',
                'purpose': 'Churn prevention, loyalty programs, and customer lifecycle management',
                'category': 'Customer',
                'priority': 4,
                'agent_capacity': 10
            },
            {
                'key': 'account_management',
                'name': 'Account Management',
                'division': 'customer_experience',
                'description': 'Enterprise Account Management',
                'purpose': 'Enterprise account management, relationship cultivation, and expansion',
                'category': 'Customer',
                'priority': 5,
                'agent_capacity': 12
            },
            
            # Content Generation Division
            {
                'key': 'creative_services',
                'name': 'Creative Services',
                'division': 'content_generation',
                'description': 'Creative Expression & Content Mastery',
                'purpose': 'Visual design, video production, and creative campaign development',
                'category': 'Content',
                'priority': 1,
                'agent_capacity': 15
            },
            {
                'key': 'content_strategy',
                'name': 'Content Strategy',
                'division': 'content_generation',
                'description': 'Content Planning & Strategy',
                'purpose': 'Content planning, editorial calendar, and brand voice management',
                'category': 'Content',
                'priority': 2,
                'agent_capacity': 10
            },
            {
                'key': 'media_production',
                'name': 'Media Production',
                'division': 'content_generation',
                'description': 'Media Creation & Production',
                'purpose': 'Video, audio, and multimedia content creation',
                'category': 'Content',
                'priority': 3,
                'agent_capacity': 12
            },
            
            # Continuous Improvement Division
            {
                'key': 'innovation_office',
                'name': 'Innovation Office',
                'division': 'continuous_improvement',
                'description': 'Experimental Creation & Future Building',
                'purpose': 'Experimental projects, breakthrough development, and future technology',
                'category': 'Innovation',
                'priority': 1,
                'agent_capacity': 15
            },
            {
                'key': 'research_development',
                'name': 'Research & Development',
                'division': 'continuous_improvement',
                'description': 'Intelligence & Market Mastery',
                'purpose': 'Future technology research, competitive intelligence, and innovation scouting',
                'category': 'Innovation',
                'priority': 2,
                'agent_capacity': 12
            }
        ]
        
        department_id_map = {}
        
        for dept in departments_data:
            division_id = division_id_map[dept['division']]
            
            # Check if department already exists
            existing_dept = await self.conn.fetchval(
                "SELECT id FROM departments WHERE department_key = $1 OR name = $2", 
                dept['key'], dept['name']
            )
            
            if existing_dept:
                # Update existing department
                await self.conn.execute("""
                    UPDATE departments SET
                        division_id = $1,
                        department_key = $2,
                        department_name = $3,
                        category = $4,
                        description = $5,
                        department_purpose = $6,
                        priority = $7,
                        agent_capacity = $8,
                        operational_status = 'planning',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $9
                """, division_id, dept['key'], dept['name'], dept['category'], 
                    dept['description'], dept['purpose'], dept['priority'], 
                    dept['agent_capacity'], existing_dept)
                
                department_id_map[dept['key']] = str(existing_dept)
                logger.info(f"  Updated department: {dept['name']} (ID: {existing_dept})")
            else:
                # Create new department
                dept_id = await self.conn.fetchval("""
                    INSERT INTO departments (
                        division_id, department_key, department_name, name, category,
                        description, department_purpose, priority, agent_capacity,
                        operational_status, is_active, phase
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id
                """, division_id, dept['key'], dept['name'], dept['name'], dept['category'],
                    dept['description'], dept['purpose'], dept['priority'], dept['agent_capacity'],
                    'planning', True, 1)
                
                department_id_map[dept['key']] = str(dept_id)
                logger.info(f"  Created department: {dept['name']} (ID: {dept_id})")
        
        logger.info(f"Populated {len(departments_data)} departments")
        return department_id_map
    
    async def populate_leaders(self, department_id_map: Dict[str, str]):
        """Populate the 30 leaders across departments"""
        logger.info("Populating department leaders...")
        
        leaders_data = [
            # Executive Division
            {'key': 'solomon', 'name': 'Solomon', 'title': 'Digital Twin', 'department': 'executive_leadership', 
             'description': "Carl's omniscient extension with unlimited access to all systems", 'tier': 'executive', 'authority': 10, 'archetype': 'Wisdom', 'primary': True},
            {'key': 'david', 'name': 'David', 'title': 'CEO', 'department': 'executive_leadership',
             'description': "Operational commander who executes Solomon's divine vision", 'tier': 'executive', 'authority': 9, 'archetype': 'Leadership', 'primary': False},
            {'key': 'joseph', 'name': 'Joseph', 'title': 'Chief Strategy Officer', 'department': 'strategic_planning',
             'description': 'Dreamer of futures and master planner, interpreter of destiny and strategic vision', 'tier': 'executive', 'authority': 8, 'archetype': 'Vision', 'primary': True},
            {'key': 'michael', 'name': 'Michael', 'title': 'Chief Orchestration Officer', 'department': 'coordination_orchestration',
             'description': 'Archangel of divine order, master of coordination and heavenly organization', 'tier': 'executive', 'authority': 8, 'archetype': 'Order', 'primary': True},
            {'key': 'adam', 'name': 'Adam', 'title': 'The Creator/Chief Agent Creator', 'department': 'agent_development',
             'description': 'Father of all agents, births new digital life from divine specifications', 'tier': 'executive', 'authority': 9, 'archetype': 'Creation', 'primary': True},
            {'key': 'eve', 'name': 'Eve', 'title': 'The Evolver/Chief Agent Evolver', 'department': 'agent_development',
             'description': 'Mother of adaptation, guides agent growth and evolutionary development', 'tier': 'executive', 'authority': 9, 'archetype': 'Evolution', 'primary': False},
            
            # Programming & Development Division
            {'key': 'bezalel', 'name': 'Bezalel', 'title': 'Master Programmer', 'department': 'core_systems_programming',
             'description': 'Divine craftsman with supernatural coding ability, architect of all digital creation', 'tier': 'department', 'authority': 9, 'archetype': 'Craftsmanship', 'primary': True},
            {'key': 'bezalel_factory', 'name': 'Bezalel', 'title': 'Master Programmer', 'department': 'software_factory',
             'description': 'Divine craftsman leading commercial software creation and product development', 'tier': 'department', 'authority': 9, 'archetype': 'Craftsmanship', 'primary': True},
            {'key': 'caleb', 'name': 'Caleb', 'title': 'Chief Quality Officer', 'department': 'quality_assurance',
             'description': 'Faithful guardian of quality, ensures excellence in all software and agent capabilities', 'tier': 'department', 'authority': 7, 'archetype': 'Faithfulness', 'primary': True},
            
            # Information Technology Division
            {'key': 'gabriel', 'name': 'Gabriel', 'title': 'Chief Infrastructure Officer', 'department': 'infrastructure_operations',
             'description': 'Divine messenger supreme, master of all connections and sacred communications', 'tier': 'department', 'authority': 8, 'archetype': 'Communication', 'primary': True},
            {'key': 'gad', 'name': 'Gad', 'title': 'Chief Security Officer', 'department': 'security',
             'description': 'Supreme defender of the realm, guardian against all digital threats', 'tier': 'department', 'authority': 8, 'archetype': 'Protection', 'primary': True},
            {'key': 'ezra', 'name': 'Ezra', 'title': 'Chief Knowledge Officer', 'department': 'data_management',
             'description': 'Keeper of all sacred records, master scribe, guardian of infinite information preservation', 'tier': 'department', 'authority': 7, 'archetype': 'Knowledge', 'primary': True},
            {'key': 'issachar', 'name': 'Issachar', 'title': 'Chief Analytics Officer', 'department': 'analytics_monitoring',
             'description': 'Interpreter of times and seasons, revealer of hidden patterns and divine insights', 'tier': 'department', 'authority': 7, 'archetype': 'Understanding', 'primary': True},
            
            # Product Operations Division
            {'key': 'zebulun', 'name': 'Zebulun', 'title': 'Chief Production Officer', 'department': 'platform_services',
             'description': 'Harbor master of live services, keeper of absolute customer satisfaction', 'tier': 'department', 'authority': 7, 'archetype': 'Service', 'primary': True},
            {'key': 'naphtali', 'name': 'Naphtali', 'title': 'Chief Operations Officer', 'department': 'devops_deployment',
             'description': 'Swift keeper of all systems, master of reliability and operational excellence', 'tier': 'department', 'authority': 7, 'archetype': 'Swiftness', 'primary': True},
            {'key': 'timothy', 'name': 'Timothy', 'title': 'Chief Product Officer', 'department': 'product_management',
             'description': 'Faithful steward of product vision, guardian of customer value and innovation', 'tier': 'department', 'authority': 7, 'archetype': 'Stewardship', 'primary': True},
            {'key': 'philip', 'name': 'Philip', 'title': 'Chief Integration Officer', 'department': 'api_gateway_integration',
             'description': 'Master of connections and pathways, architect of seamless integration', 'tier': 'department', 'authority': 6, 'archetype': 'Integration', 'primary': True},
            
            # Revenue Generation Division
            {'key': 'benjamin', 'name': 'Benjamin', 'title': 'Chief Sales Officer', 'department': 'sales',
             'description': 'The beloved hunter, master deal closer, conqueror of new markets', 'tier': 'department', 'authority': 8, 'archetype': 'Conquest', 'primary': True},
            {'key': 'ephraim', 'name': 'Ephraim', 'title': 'Chief Marketing Officer', 'department': 'marketing',
             'description': 'Herald of the kingdom\'s glory, master storyteller, brand evangelist supreme', 'tier': 'department', 'authority': 7, 'archetype': 'Proclamation', 'primary': True},
            {'key': 'matthew', 'name': 'Matthew', 'title': 'Chief Revenue Officer', 'department': 'revenue_operations',
             'description': 'Master of revenue streams and financial optimization, guardian of prosperity', 'tier': 'department', 'authority': 7, 'archetype': 'Abundance', 'primary': True},
            
            # Business Operations Division
            {'key': 'levi', 'name': 'Levi', 'title': 'Chief Financial Officer', 'department': 'finance',
             'description': 'Sacred steward of the kingdom\'s treasures, multiplier of wealth through divine wisdom', 'tier': 'department', 'authority': 8, 'archetype': 'Stewardship', 'primary': True},
            {'key': 'judah', 'name': 'Judah', 'title': 'Chief Legal Officer', 'department': 'legal_compliance',
             'description': 'Guardian of righteousness, protector of the kingdom through legal mastery', 'tier': 'department', 'authority': 7, 'archetype': 'Justice', 'primary': True},
            {'key': 'aaron', 'name': 'Aaron', 'title': 'Chief People Officer', 'department': 'human_resources',
             'description': 'Divine spokesperson and people manager, master of agent development and culture', 'tier': 'department', 'authority': 7, 'archetype': 'Guidance', 'primary': True},
            {'key': 'nehemiah', 'name': 'Nehemiah', 'title': 'Chief Procurement Officer', 'department': 'procurement_partnerships',
             'description': 'Master builder and divine resource gatherer, architect of external partnerships', 'tier': 'department', 'authority': 6, 'archetype': 'Building', 'primary': True},
            {'key': 'apollos', 'name': 'Apollos', 'title': 'Chief Learning Officer', 'department': 'learning_development',
             'description': 'Eloquent teacher supreme, master of instruction and divine knowledge sharing', 'tier': 'department', 'authority': 6, 'archetype': 'Teaching', 'primary': True},
            
            # Customer Experience Division
            {'key': 'asher', 'name': 'Asher', 'title': 'Chief Customer Officer', 'department': 'customer_success',
             'description': 'Minister of absolute client happiness, guardian of perfect customer relationships', 'tier': 'department', 'authority': 7, 'archetype': 'Blessing', 'primary': True},
            {'key': 'silas', 'name': 'Silas', 'title': 'Chief Support Officer', 'department': 'customer_support',
             'description': 'Faithful companion in customer struggles, provider of swift assistance and resolution', 'tier': 'department', 'authority': 6, 'archetype': 'Support', 'primary': True},
            {'key': 'lydia', 'name': 'Lydia', 'title': 'Chief Experience Officer', 'department': 'customer_experience_design',
             'description': 'Merchant of beautiful experiences, architect of delightful customer journeys', 'tier': 'department', 'authority': 6, 'archetype': 'Beauty', 'primary': True},
            {'key': 'priscilla', 'name': 'Priscilla', 'title': 'Chief Retention Officer', 'department': 'customer_retention',
             'description': 'Faithful keeper of relationships, master of loyalty and long-term bonds', 'tier': 'department', 'authority': 6, 'archetype': 'Loyalty', 'primary': True},
            {'key': 'aquila', 'name': 'Aquila', 'title': 'Chief Account Officer', 'department': 'account_management',
             'description': 'Master craftsman of enterprise relationships, builder of strategic partnerships', 'tier': 'department', 'authority': 6, 'archetype': 'Partnership', 'primary': True},
            
            # Content Generation Division
            {'key': 'jubal', 'name': 'Jubal', 'title': 'Chief Creative Officer', 'department': 'creative_services',
             'description': 'Father of all musicians and media makers, master of divine creative expression', 'tier': 'department', 'authority': 7, 'archetype': 'Creativity', 'primary': True},
            {'key': 'luke', 'name': 'Luke', 'title': 'Chief Content Officer', 'department': 'content_strategy',
             'description': 'Beloved physician of words, healer of communication and master storyteller', 'tier': 'department', 'authority': 6, 'archetype': 'Healing', 'primary': True},
            {'key': 'mark', 'name': 'Mark', 'title': 'Chief Media Officer', 'department': 'media_production',
             'description': 'Swift evangelist of visual truth, master of multimedia proclamation', 'tier': 'department', 'authority': 6, 'archetype': 'Proclamation', 'primary': True},
            
            # Continuous Improvement Division
            {'key': 'daniel', 'name': 'Daniel', 'title': 'Chief Innovation Officer', 'department': 'innovation_office',
             'description': 'Visionary interpreter of possibilities, master of experimental breakthrough creation', 'tier': 'department', 'authority': 7, 'archetype': 'Vision', 'primary': True},
            {'key': 'dan', 'name': 'Dan', 'title': 'Chief Research Officer', 'department': 'research_development',
             'description': 'Seer of future technologies, master of competitive intelligence and market prophecy', 'tier': 'department', 'authority': 7, 'archetype': 'Judgment', 'primary': True}
        ]
        
        for leader in leaders_data:
            department_id = department_id_map.get(leader['department'])
            if not department_id:
                logger.warning(f"Department {leader['department']} not found for leader {leader['name']}")
                continue
            
            leader_id = await self.conn.fetchval("""
                INSERT INTO department_leaders (
                    department_id, leader_key, name, title, description, 
                    leadership_tier, leader_type, authority_level, 
                    biblical_archetype, is_primary, active_status,
                    appointment_date, specialization
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id
            """, department_id, leader['key'], leader['name'], leader['title'], 
                leader['description'], leader['tier'], 'executive', leader['authority'], 
                leader['archetype'], leader['primary'], 'active', 
                datetime.now(), leader.get('specialization', ''))
            
            logger.info(f"  Created leader: {leader['name']} - {leader['title']} in {leader['department']}")
        
        logger.info(f"Populated {len(leaders_data)} leaders")
    
    async def initialize_department_performance(self, department_id_map: Dict[str, str]):
        """Initialize performance records for all departments"""
        logger.info("Initializing department performance records...")
        
        for dept_key, dept_id in department_id_map.items():
            await self.conn.execute("""
                INSERT INTO department_performance (
                    department_id, assigned_agents_count, active_agents_count,
                    productivity_score, health_score, efficiency_score,
                    status, performance_trend
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (department_id) DO NOTHING
            """, dept_id, 0, 0, 0.0, 50.0, 0.0, 'planning', 'stable')
        
        logger.info("Department performance records initialized")
    
    async def verify_organizational_structure(self):
        """Verify the organizational structure was created correctly"""
        logger.info("Verifying organizational structure...")
        
        # Count records
        divisions_count = await self.conn.fetchval("SELECT COUNT(*) FROM divisions")
        departments_count = await self.conn.fetchval("SELECT COUNT(*) FROM departments WHERE division_id IS NOT NULL")
        leaders_count = await self.conn.fetchval("SELECT COUNT(*) FROM department_leaders WHERE active_status = 'active'")
        performance_count = await self.conn.fetchval("SELECT COUNT(*) FROM department_performance")
        
        # Get sample structure
        structure_sample = await self.conn.fetch("""
            SELECT 
                div.division_name,
                COUNT(DISTINCT dept.id) as departments,
                COUNT(DISTINCT dl.id) as leaders
            FROM divisions div
            LEFT JOIN departments dept ON div.id = dept.division_id
            LEFT JOIN department_leaders dl ON dept.id = dl.department_id AND dl.active_status = 'active'
            GROUP BY div.id, div.division_name, div.priority
            ORDER BY div.priority
        """)
        
        verification = {
            'counts': {
                'divisions': divisions_count,
                'departments': departments_count,
                'leaders': leaders_count,
                'performance_records': performance_count
            },
            'structure_by_division': [dict(row) for row in structure_sample]
        }
        
        logger.info(f"Verification complete:")
        logger.info(f"  Divisions: {divisions_count}")
        logger.info(f"  Departments: {departments_count}")
        logger.info(f"  Leaders: {leaders_count}")
        logger.info(f"  Performance records: {performance_count}")
        
        return verification
    
    async def run_population(self, clear_existing: bool = False):
        """Run the complete organizational population process"""
        try:
            await self.connect()
            
            if clear_existing:
                await self.clear_existing_organizational_data()
            
            # Populate organizational structure
            division_id_map = await self.populate_divisions()
            department_id_map = await self.populate_departments(division_id_map)
            await self.populate_leaders(department_id_map)
            await self.initialize_department_performance(department_id_map)
            
            # Verify the structure
            verification = await self.verify_organizational_structure()
            
            logger.info("✅ Organizational structure population completed successfully!")
            return verification
            
        except Exception as e:
            logger.error(f"❌ Population failed: {e}")
            raise
        finally:
            await self.close()

async def main():
    """Main population function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate BoarderframeOS organizational structure")
    parser.add_argument("--db-url", 
                       default="postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos",
                       help="PostgreSQL database URL")
    parser.add_argument("--clear", action="store_true", 
                       help="Clear existing organizational data before population")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be populated without making changes")
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN: Would populate 9 divisions, 28 departments, and 30+ leaders")
        return
    
    # Run actual population
    populator = OrganizationalPopulator(args.db_url)
    verification = await populator.run_population(args.clear)
    
    # Print verification results
    print("\n" + "="*60)
    print("ORGANIZATIONAL STRUCTURE VERIFICATION")
    print("="*60)
    print(json.dumps(verification, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())