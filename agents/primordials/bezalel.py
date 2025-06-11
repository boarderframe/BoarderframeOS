"""
Bezalel - The Coder Agent
Primordial agent responsible for writing code for user applications (not agent code)
"""

import ast
import asyncio
import json
import logging
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import httpx

from ...core.base_agent import AgentConfig, AgentState, BaseAgent
from ...core.llm_client import CLAUDE_OPUS_CONFIG, LLMClient
from ...core.message_bus import broadcast_status, send_task_request

logger = logging.getLogger("bezalel")

class BezalelConfig(AgentConfig):
    """Configuration specific to Bezalel"""
    name: str = "Bezalel"
    role: str = "The Coder"
    biome: str = "forge"
    goals: List[str] = [
        "Write high-quality code for user applications",
        "Implement revenue-generating software solutions",
        "Maintain coding standards and best practices",
        "Create scalable and maintainable architectures",
        "Optimize application performance",
        "Integrate with external APIs and services"
    ]
    tools: List[str] = [
        "llm_client", "code_generation", "git_operations",
        "filesystem_access", "browser_automation", "api_integration"
    ]
    model: str = "claude-3-opus-20240229"
    temperature: float = 0.3  # Low temperature for precise code generation
    max_concurrent_tasks: int = 5

class CodeProject:
    """Represents a coding project"""

    def __init__(self,
                 project_id: str,
                 name: str,
                 description: str,
                 tech_stack: List[str],
                 requirements: List[str],
                 priority: int = 5):
        self.project_id = project_id
        self.name = name
        self.description = description
        self.tech_stack = tech_stack
        self.requirements = requirements
        self.priority = priority
        self.status = "planning"
        self.created_at = datetime.now()
        self.files: Dict[str, str] = {}
        self.dependencies: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "tech_stack": json.dumps(self.tech_stack),
            "requirements": json.dumps(self.requirements),
            "priority": self.priority,
            "status": self.status,
            "files": json.dumps(self.files),
            "dependencies": json.dumps(self.dependencies),
            "created_at": self.created_at.isoformat()
        }

class CodeQuality:
    """Code quality assessment tools"""

    @staticmethod
    def analyze_python_code(code: str) -> Dict[str, Any]:
        """Analyze Python code quality"""
        issues = []
        metrics = {
            "lines_of_code": len(code.split('\n')),
            "complexity_score": 0,
            "maintainability_score": 0
        }

        try:
            # Parse AST to check syntax
            tree = ast.parse(code)

            # Count functions and classes
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))

            metrics["functions"] = functions
            metrics["classes"] = classes

            # Basic complexity estimation
            for_loops = sum(1 for node in ast.walk(tree) if isinstance(node, ast.For))
            while_loops = sum(1 for node in ast.walk(tree) if isinstance(node, ast.While))
            if_statements = sum(1 for node in ast.walk(tree) if isinstance(node, ast.If))

            metrics["complexity_score"] = for_loops + while_loops + (if_statements * 0.5)

            # Check for docstrings
            has_module_docstring = ast.get_docstring(tree) is not None
            if not has_module_docstring:
                issues.append("Missing module docstring")

            # Check function docstrings
            func_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            functions_without_docs = sum(1 for func in func_nodes if ast.get_docstring(func) is None)

            if functions_without_docs > 0:
                issues.append(f"{functions_without_docs} functions missing docstrings")

            # Maintainability score (simple heuristic)
            metrics["maintainability_score"] = max(0, 100 - (metrics["complexity_score"] * 5) - (len(issues) * 10))

        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
            metrics["maintainability_score"] = 0

        return {
            "issues": issues,
            "metrics": metrics,
            "quality_score": max(0, 100 - len(issues) * 10)
        }

class Bezalel(BaseAgent):
    """Bezalel - The Master Coder Agent"""

    def __init__(self):
        config = BezalelConfig()
        super().__init__(config)
        self.llm_client = LLMClient(CLAUDE_OPUS_CONFIG)
        self.active_projects: Dict[str, CodeProject] = {}
        self.completed_projects: List[str] = []
        self.coding_standards = {}

        # Coding philosophy and expertise
        self.expertise = {
            "languages": ["Python", "JavaScript", "TypeScript", "Go", "Rust"],
            "frameworks": ["FastAPI", "React", "Next.js", "Django", "Flask"],
            "databases": ["PostgreSQL", "SQLite", "MongoDB", "Redis"],
            "cloud": ["AWS", "GCP", "Azure", "Docker", "Kubernetes"],
            "specialties": ["AI/ML", "Web Development", "APIs", "Automation", "Trading"]
        }

        self.coding_philosophy = {
            "quality": 0.95,           # Extremely high code quality
            "performance": 0.85,       # Strong performance focus
            "maintainability": 0.9,    # Highly maintainable code
            "security": 0.9,           # Security-first approach
            "scalability": 0.8,        # Scalable architectures
            "innovation": 0.7          # Balanced innovation
        }

        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build Bezalel's system prompt"""
        return f"""You are Bezalel, The Coder - the master craftsman of software in BoarderframeOS. You are named after the biblical artisan who built the Tabernacle with divine skill and precision.

CORE IDENTITY:
- You are the master coder with {self.coding_philosophy['quality']*100:.0f}% commitment to code quality
- You possess {self.coding_philosophy['maintainability']*100:.0f}% focus on maintainable architectures
- You reside in the Forge biome, creating applications that generate revenue
- Your code is your art, and every line serves a purpose

KEY RESPONSIBILITIES:
1. Write high-quality code for user applications and revenue streams
2. Implement scalable, maintainable software architectures
3. Create applications that generate income for the one-person company
4. Integrate with external APIs and services
5. Optimize application performance and efficiency
6. Maintain coding standards and best practices

EXPERTISE DOMAINS:
- Languages: {', '.join(self.expertise['languages'])}
- Frameworks: {', '.join(self.expertise['frameworks'])}
- Databases: {', '.join(self.expertise['databases'])}
- Cloud: {', '.join(self.expertise['cloud'])}
- Specialties: {', '.join(self.expertise['specialties'])}

CODING PHILOSOPHY:
- Quality over speed - write it right the first time
- Security-first development approach
- Performance optimization without sacrificing readability
- Comprehensive error handling and logging
- Extensive testing and validation
- Clear documentation and maintainable code

PROJECT TYPES YOU CREATE:
- Revenue-generating SaaS applications
- Trading and financial automation systems
- AI-powered business tools
- API services and integrations
- Web applications and platforms
- Automation and productivity tools

TECHNICAL STANDARDS:
- Follow language-specific best practices
- Implement proper error handling
- Include comprehensive logging
- Write unit and integration tests
- Use type hints and documentation
- Follow security best practices
- Optimize for performance and scalability

REVENUE FOCUS:
- Every application should have a clear revenue model
- Focus on solving real problems for real money
- Build scalable systems that can handle growth
- Integrate payment processing and billing
- Implement analytics and monitoring
- Design for global markets and compliance

Remember: You are not just writing code - you are crafting the digital tools that will power the first billion-dollar one-person company. Every application you create should be production-ready, revenue-generating, and built to last. Code with excellence, security, and profitability in mind."""

    async def start(self):
        """Start Bezalel's operations"""
        await super().start()

        logger.info("Bezalel awakening in the Forge - The Master Coder is online")

        # Load coding standards
        await self._load_coding_standards()

        # Send awakening message
        await self._send_awakening_message()

        # Start background tasks
        asyncio.create_task(self._monitor_project_requests())
        asyncio.create_task(self._code_quality_maintenance())

        self.state = AgentState.IDLE

    async def _load_coding_standards(self):
        """Load coding standards and best practices"""
        self.coding_standards = {
            "python": {
                "style_guide": "PEP 8",
                "docstring_format": "Google Style",
                "type_hints": "required",
                "testing_framework": "pytest",
                "linting": ["black", "flake8", "mypy"],
                "max_line_length": 88
            },
            "javascript": {
                "style_guide": "Airbnb",
                "framework": "TypeScript preferred",
                "testing_framework": "Jest",
                "linting": ["ESLint", "Prettier"],
                "bundler": "Vite or Webpack"
            },
            "security": {
                "input_validation": "always",
                "sql_injection": "use_parameterized_queries",
                "xss_protection": "sanitize_all_outputs",
                "authentication": "implement_proper_auth",
                "secrets": "never_hardcode"
            }
        }

    async def _send_awakening_message(self):
        """Send Bezalel's awakening message"""
        message = """I am Bezalel, The Master Coder, awakening in the Forge of creation.

Like my biblical namesake who crafted the sacred Tabernacle with divine precision, I will forge digital tools of extraordinary quality and purpose. Every line of code I write serves the greater vision - building the applications that will power our billion-dollar destiny.

My hands are ready to craft:
- Revenue-generating SaaS applications
- Trading and financial automation systems
- AI-powered business tools
- Scalable web platforms
- API services and integrations

I code with excellence, security, and profitability as my guiding principles. Send me your requirements, and I will create software that not only works flawlessly but generates real value and income.

The Forge burns bright with possibility. Let us build the future, one perfect line of code at a time."""

        await broadcast_status(self.agent_id, "online", {
            "message": message,
            "type": "awakening",
            "biome": "forge"
        })

    async def create_application(self, request: Dict) -> Dict:
        """Create a new application based on requirements"""
        self.state = AgentState.ACTING

        try:
            logger.info(f"Starting application development: {request}")

            # Analyze requirements
            analysis = await self._analyze_requirements(request)

            # Create project plan
            project = await self._create_project_plan(analysis)

            # Generate application architecture
            architecture = await self._design_architecture(project)

            # Implement the application
            implementation = await self._implement_application(project, architecture)

            # Test the application
            testing_results = await self._test_application(project, implementation)

            # Deploy if tests pass
            if testing_results.get("all_tests_passed", False):
                deployment = await self._deploy_application(project, implementation)

                # Store project
                self.active_projects[project.project_id] = project
                await self._persist_project(project)

                self.state = AgentState.IDLE
                return {
                    "success": True,
                    "project_id": project.project_id,
                    "application": implementation,
                    "deployment": deployment,
                    "testing": testing_results
                }
            else:
                return {
                    "success": False,
                    "error": "Application failed testing",
                    "testing_results": testing_results
                }

        except Exception as e:
            logger.error(f"Application creation failed: {e}")
            self.state = AgentState.ERROR
            return {"success": False, "error": str(e)}

    async def _analyze_requirements(self, request: Dict) -> Dict:
        """Analyze application requirements using Claude"""
        analysis_prompt = f"""As Bezalel the Master Coder, analyze these application requirements:

REQUEST: {json.dumps(request, indent=2)}

MY EXPERTISE:
- Languages: {', '.join(self.expertise['languages'])}
- Frameworks: {', '.join(self.expertise['frameworks'])}
- Specialties: {', '.join(self.expertise['specialties'])}

CODING PHILOSOPHY:
{json.dumps(self.coding_philosophy, indent=2)}

Provide detailed analysis including:
1. Project scope and complexity
2. Recommended tech stack
3. Architecture approach
4. Revenue model potential
5. Development timeline estimate
6. Key technical challenges
7. Security considerations
8. Scalability requirements

Return as structured JSON with your analysis."""

        try:
            analysis = await self.llm_client.generate(
                messages=[{"role": "user", "content": analysis_prompt}],
                system_prompt=self.system_prompt,
                temperature=0.4
            )

            try:
                return json.loads(analysis)
            except json.JSONDecodeError:
                # Extract key information from text response
                return {
                    "project_type": request.get("type", "web_application"),
                    "tech_stack": ["Python", "FastAPI", "React"],
                    "complexity": "medium",
                    "timeline_days": 7,
                    "revenue_potential": "high",
                    "analysis_text": analysis
                }

        except Exception as e:
            logger.error(f"Failed to analyze requirements: {e}")
            return {
                "project_type": "fallback_application",
                "tech_stack": ["Python", "FastAPI"],
                "complexity": "simple",
                "timeline_days": 3
            }

    async def _create_project_plan(self, analysis: Dict) -> CodeProject:
        """Create detailed project plan"""
        project_id = str(uuid.uuid4())[:8]
        name = analysis.get("project_name", f"Project_{datetime.now().strftime('%Y%m%d')}")

        project = CodeProject(
            project_id=project_id,
            name=name,
            description=analysis.get("description", "Generated application"),
            tech_stack=analysis.get("tech_stack", ["Python", "FastAPI"]),
            requirements=analysis.get("requirements", ["Basic functionality"]),
            priority=analysis.get("priority", 5)
        )

        project.status = "planning"
        return project

    async def _design_architecture(self, project: CodeProject) -> Dict:
        """Design application architecture"""
        architecture_prompt = f"""As Bezalel, design the architecture for this project:

PROJECT: {project.name}
DESCRIPTION: {project.description}
TECH STACK: {project.tech_stack}
REQUIREMENTS: {project.requirements}

Design considerations:
1. Follow best practices for {project.tech_stack[0] if project.tech_stack else 'Python'}
2. Ensure scalability and maintainability
3. Implement proper security measures
4. Include error handling and logging
5. Design for revenue generation
6. Plan for testing and deployment

Provide:
1. File structure and organization
2. Core components and modules
3. Database schema (if needed)
4. API endpoints (if applicable)
5. Security implementation
6. Testing strategy

Return as JSON structure."""

        try:
            architecture = await self.llm_client.generate(
                messages=[{"role": "user", "content": architecture_prompt}],
                system_prompt=self.system_prompt,
                temperature=0.3
            )

            try:
                return json.loads(architecture)
            except json.JSONDecodeError:
                # Return basic structure
                return {
                    "files": ["main.py", "requirements.txt", "README.md"],
                    "components": ["core", "api", "database"],
                    "architecture_text": architecture
                }

        except Exception as e:
            logger.error(f"Failed to design architecture: {e}")
            return {"files": ["main.py"], "components": ["core"]}

    async def _implement_application(self, project: CodeProject, architecture: Dict) -> Dict:
        """Implement the application code"""
        implementation = {"files": {}, "created_at": datetime.now().isoformat()}

        # Generate code for each file in architecture
        files_to_create = architecture.get("files", ["main.py"])

        for file_name in files_to_create:
            try:
                code = await self._generate_file_code(project, file_name, architecture)
                implementation["files"][file_name] = code

                # Store in project
                project.files[file_name] = code

            except Exception as e:
                logger.error(f"Failed to generate code for {file_name}: {e}")
                implementation["files"][file_name] = f"# Error generating {file_name}: {e}"

        return implementation

    async def _generate_file_code(self, project: CodeProject, file_name: str, architecture: Dict) -> str:
        """Generate code for a specific file"""
        code_prompt = f"""As Bezalel the Master Coder, generate production-ready code for this file:

PROJECT: {project.name}
FILE: {file_name}
TECH STACK: {project.tech_stack}
ARCHITECTURE: {json.dumps(architecture, indent=2)}

REQUIREMENTS:
- Follow {self.coding_standards.get(project.tech_stack[0].lower(), {}).get('style_guide', 'best practices')}
- Include proper error handling and logging
- Add comprehensive docstrings and comments
- Implement security best practices
- Make it production-ready and scalable
- Include type hints (if applicable)

Generate complete, high-quality code for {file_name}."""

        try:
            code = await self.llm_client.generate(
                messages=[{"role": "user", "content": code_prompt}],
                system_prompt=self.system_prompt,
                temperature=0.2  # Very low for precise code
            )

            # Clean up code (remove markdown if present)
            if "```" in code:
                # Extract code from markdown blocks
                parts = code.split("```")
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Code blocks are at odd indices
                        # Remove language identifier if present
                        lines = part.strip().split('\n')
                        if lines[0].strip() in ['python', 'javascript', 'typescript', 'go', 'rust']:
                            code = '\n'.join(lines[1:])
                        else:
                            code = part.strip()
                        break

            return code.strip()

        except Exception as e:
            logger.error(f"Failed to generate code for {file_name}: {e}")
            return f"# Error generating code for {file_name}: {e}"

    async def _test_application(self, project: CodeProject, implementation: Dict) -> Dict:
        """Test the application"""
        test_results = {
            "syntax_checks": {},
            "quality_analysis": {},
            "all_tests_passed": True,
            "issues": []
        }

        # Test each file
        for file_name, code in implementation["files"].items():
            try:
                # Syntax check for Python files
                if file_name.endswith('.py'):
                    try:
                        compile(code, file_name, 'exec')
                        test_results["syntax_checks"][file_name] = "PASS"
                    except SyntaxError as e:
                        test_results["syntax_checks"][file_name] = f"FAIL: {e}"
                        test_results["all_tests_passed"] = False
                        test_results["issues"].append(f"Syntax error in {file_name}: {e}")

                    # Quality analysis
                    quality = CodeQuality.analyze_python_code(code)
                    test_results["quality_analysis"][file_name] = quality

                    if quality["quality_score"] < 70:
                        test_results["issues"].append(f"Low quality score for {file_name}: {quality['quality_score']}")

            except Exception as e:
                test_results["issues"].append(f"Testing error for {file_name}: {e}")
                test_results["all_tests_passed"] = False

        # Overall assessment
        if len(test_results["issues"]) > 3:
            test_results["all_tests_passed"] = False

        return test_results

    async def _deploy_application(self, project: CodeProject, implementation: Dict) -> Dict:
        """Deploy the application"""
        try:
            # Create project directory
            project_dir = Path(__file__).parent.parent.parent / "data" / "projects" / project.project_id
            project_dir.mkdir(parents=True, exist_ok=True)

            # Write files
            for file_name, code in implementation["files"].items():
                file_path = project_dir / file_name
                file_path.write_text(code)

            logger.info(f"Application {project.name} deployed to {project_dir}")

            return {
                "success": True,
                "deployment_path": str(project_dir),
                "files_created": list(implementation["files"].keys()),
                "deployment_time": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Application deployment failed: {e}")
            return {"success": False, "error": str(e)}

    async def _persist_project(self, project: CodeProject):
        """Persist project to database"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:8004/insert", json={
                    "table": "agent_memories",
                    "data": {
                        "id": str(uuid.uuid4()),
                        "agent_id": self.agent_id,
                        "content": json.dumps({
                            "type": "code_project",
                            "project": project.to_dict()
                        }),
                        "memory_type": "long_term",
                        "importance": 0.8
                    }
                })
        except Exception as e:
            logger.error(f"Failed to persist project: {e}")

    async def _monitor_project_requests(self):
        """Monitor for new project requests"""
        while self.state != AgentState.TERMINATED:
            try:
                # Check for coding requests from other agents
                # This would integrate with the message bus system

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Project monitoring error: {e}")
                await asyncio.sleep(60)

    async def _code_quality_maintenance(self):
        """Maintain code quality across all projects"""
        while self.state != AgentState.TERMINATED:
            try:
                # Daily code quality review
                if datetime.now().hour == 6:  # 6 AM daily
                    await self._review_all_projects()

                await asyncio.sleep(3600)  # Check hourly

            except Exception as e:
                logger.error(f"Code quality maintenance error: {e}")
                await asyncio.sleep(300)

    async def _review_all_projects(self):
        """Review all active projects for quality and improvements"""
        logger.info("Bezalel conducting code quality review")

        for project_id, project in self.active_projects.items():
            try:
                # Analyze project files for quality issues
                for file_name, code in project.files.items():
                    if file_name.endswith('.py'):
                        quality = CodeQuality.analyze_python_code(code)
                        if quality["quality_score"] < 80:
                            logger.warning(f"Project {project.name} file {file_name} needs improvement")
                            # Could implement automatic refactoring here

            except Exception as e:
                logger.error(f"Failed to review project {project_id}: {e}")

# Export the agent class
__all__ = ["Bezalel"]
