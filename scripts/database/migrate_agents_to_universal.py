#!/usr/bin/env python3
"""
Migrate existing agents to Universal Agent architecture
This script helps transition from individual agent implementations to database-driven configs
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))


async def run_migration():
    """Run the agent configuration migration"""
    print("=== BoarderframeOS Agent Migration ===")
    print("Migrating to Universal Agent Architecture...")
    
    # Connect to PostgreSQL
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='boarderframe',
        password='boarderframe123',
        database='boarderframeos'
    )
    
    try:
        # First, create the schema if it doesn't exist
        print("\n1. Creating agent_configs schema...")
        
        migration_file = Path(__file__).parent.parent.parent / "migrations" / "003_agent_configs_schema.sql"
        if migration_file.exists():
            with open(migration_file, 'r') as f:
                schema_sql = f.read()
                
            await conn.execute(schema_sql)
            print("✓ Schema created successfully")
        else:
            print("✗ Migration file not found")
            return
            
        # Check current data
        print("\n2. Checking existing agent configurations...")
        existing_count = await conn.fetchval("SELECT COUNT(*) FROM agent_configs")
        print(f"✓ Found {existing_count} existing agent configurations")
        
        # Update development status based on actual implementation
        print("\n3. Updating development status based on implementation...")
        
        # Mark implemented agents
        implemented_agents = ['Solomon', 'David', 'Adam', 'Eve', 'Bezalel']
        for agent in implemented_agents:
            await conn.execute("""
                UPDATE agent_configs 
                SET development_status = 'in_development'
                WHERE name = $1
            """, agent)
            
        print(f"✓ Updated {len(implemented_agents)} agents to 'in_development' status")
        
        # Create wrapper scripts for existing agents
        print("\n4. Creating compatibility wrappers...")
        
        wrapper_template = '''#!/usr/bin/env python3
"""
{agent_name} - Compatibility wrapper for Universal Agent
This wrapper maintains backward compatibility while using the new architecture
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.universal_agent import UniversalAgent
from core.agent_launcher import agent_launcher


class {class_name}(UniversalAgent):
    """Compatibility wrapper for {agent_name}"""
    
    def __init__(self):
        # Initialize with agent name to load from database
        super().__init__(agent_name="{agent_name}")
        
    # Add any agent-specific methods here if needed
    # Most functionality is now handled by UniversalAgent


async def main():
    """Run {agent_name} agent"""
    # Initialize launcher
    await agent_launcher.initialize()
    
    # Create and start agent
    agent = {class_name}()
    
    try:
        print(f"Starting {{agent.name}} ({{agent.config.role}})...")
        print(f"Department: {{agent.config.department}}")
        print(f"LLM Model: {{agent.llm_model}}")
        print(f"Personality: {{agent.personality.get('traits', [])}}")
        
        await agent.start()
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\\nShutting down...")
        await agent.stop()
        await agent_launcher.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
'''
        
        wrappers_created = 0
        for agent in implemented_agents:
            wrapper_dir = Path(f"agents/{agent.lower()}")
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            
            wrapper_file = wrapper_dir / f"{agent.lower()}_universal.py"
            class_name = agent if agent != "CEO" else "DavidCEO"
            
            with open(wrapper_file, 'w') as f:
                f.write(wrapper_template.format(
                    agent_name=agent,
                    class_name=class_name
                ))
                
            os.chmod(wrapper_file, 0o755)
            wrappers_created += 1
            
        print(f"✓ Created {wrappers_created} compatibility wrappers")
        
        # Create example for new agent creation
        print("\n5. Creating example new agent script...")
        
        example_script = '''#!/usr/bin/env python3
"""
Example: Creating a new agent using Universal Agent architecture
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core.agent_launcher import agent_launcher


async def create_customer_service_agent():
    """Example: Create a customer service agent"""
    
    # Initialize launcher
    await agent_launcher.initialize()
    
    # Create new agent
    agent = await agent_launcher.create_new_agent(
        name="Miriam",
        role="Customer Service Lead",
        department="Sales",
        personality_traits=["helpful", "patient", "empathetic", "solution-oriented"],
        goals=[
            "Resolve customer issues quickly",
            "Maintain high satisfaction ratings",
            "Identify upsell opportunities",
            "Build lasting customer relationships"
        ],
        tools=[
            "customer_lookup",
            "ticket_management", 
            "knowledge_base",
            "escalation",
            "sentiment_analysis"
        ],
        llm_model="claude-3-haiku",  # Use faster model for customer service
        system_prompt="""You are Miriam, the Customer Service Lead at BoarderframeOS.
Like the biblical Miriam who led with joy and care, you help customers with patience 
and empathy. You find creative solutions to their problems while maintaining a positive, 
helpful demeanor. Your goal is to turn every interaction into a positive experience."""
    )
    
    print(f"Created new agent: {agent.name}")
    print(f"Role: {agent.config.role}")
    print(f"Department: {agent.config.department}")
    print(f"LLM Model: {agent.llm_model}")
    
    # Agent is now running and ready to handle tasks
    
    # Cleanup
    await agent_launcher.cleanup()


async def update_agent_models_by_complexity():
    """Example: Update agent models based on task complexity"""
    
    await agent_launcher.initialize()
    
    # Use premium models for complex agents
    complex_agents = ["Solomon", "David", "Adam", "Eve", "Bezalel"]
    for agent in complex_agents:
        await agent_launcher.update_agent_model(agent, "claude-3-opus")
        
    # Use standard models for moderate complexity
    moderate_agents = ["Gabriel", "Michael"]
    for agent in moderate_agents:
        await agent_launcher.update_agent_model(agent, "claude-3-sonnet")
        
    # Use fast models for simple tasks
    # simple_agents = ["customer_service", "data_entry"]
    # for agent in simple_agents:
    #     await agent_launcher.update_agent_model(agent, "claude-3-haiku")
    
    print("Updated agent models based on complexity")
    
    await agent_launcher.cleanup()


async def launch_department():
    """Example: Launch all agents from a department"""
    
    await agent_launcher.initialize()
    
    # Launch all Executive department agents
    executive_agents = await agent_launcher.launch_department_agents("Executive")
    
    print(f"Launched {len(executive_agents)} Executive agents:")
    for agent in executive_agents:
        status = await agent.report_status()
        print(f"  - {agent.name}: {status['state']}")
        
    # Let them run for a bit
    await asyncio.sleep(5)
    
    # Stop all agents
    await agent_launcher.stop_all_agents()
    await agent_launcher.cleanup()


if __name__ == "__main__":
    print("Universal Agent Examples")
    print("1. Create new customer service agent")
    print("2. Update agent models by complexity") 
    print("3. Launch department agents")
    
    choice = input("\\nSelect example (1-3): ")
    
    if choice == "1":
        asyncio.run(create_customer_service_agent())
    elif choice == "2":
        asyncio.run(update_agent_models_by_complexity())
    elif choice == "3":
        asyncio.run(launch_department())
    else:
        print("Invalid choice")
'''
        
        example_file = Path("examples/universal_agent_examples.py")
        example_file.parent.mkdir(exist_ok=True)
        
        with open(example_file, 'w') as f:
            f.write(example_script)
            
        os.chmod(example_file, 0o755)
        print("✓ Created example script: examples/universal_agent_examples.py")
        
        # Summary
        print("\n=== Migration Summary ===")
        print(f"✓ Agent configuration schema created")
        print(f"✓ {existing_count} agents configured in database")
        print(f"✓ {len(implemented_agents)} agents marked as in_development")
        print(f"✓ {wrappers_created} compatibility wrappers created")
        print(f"✓ Example scripts created")
        
        print("\n=== Next Steps ===")
        print("1. Test compatibility wrappers:")
        print("   python agents/solomon/solomon_universal.py")
        print("\n2. Try creating new agents:")
        print("   python examples/universal_agent_examples.py")
        print("\n3. Launch all agents:")
        print("   python -c 'from core.agent_launcher import agent_launcher; import asyncio; asyncio.run(agent_launcher.launch_all_active_agents())'")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())