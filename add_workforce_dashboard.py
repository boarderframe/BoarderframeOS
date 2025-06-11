#!/usr/bin/env python3
"""
Add workforce dashboard section to registry display
"""

def generate_workforce_section():
    """Generate HTML for workforce dashboard section"""

    print("📊 Enhanced Registry Display with Workforce Dashboard")
    print("=" * 70)
    print("\nAdd this section after the Registry Statistics in _generate_registry_overview_html:\n")

    workforce_html = '''
                <!-- Workforce Development Dashboard -->
                <div class="card full-width" style="margin-top: 2rem;">
                    <h4 style="color: var(--accent-color); margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-users-cog"></i> Workforce Development Pipeline
                    </h4>

                    <!-- Workforce Overview -->
                    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; margin-bottom: 2rem;">
                        <div class="metric-item" style="background: linear-gradient(135deg, #10b98110, #10b98105); border: 1px solid #10b98120; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #10b981; font-size: 2rem;">{registry_data.get('workforce_stats', {}).get('total', 0)}</div>
                            <div class="metric-label">Total Workforce</div>
                        </div>
                        <div class="metric-item" style="background: linear-gradient(135deg, #06b6d410, #06b6d405); border: 1px solid #06b6d420; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #06b6d4; font-size: 2rem;">{registry_data.get('workforce_stats', {}).get('operational', 0)}</div>
                            <div class="metric-label">Operational</div>
                        </div>
                        <div class="metric-item" style="background: linear-gradient(135deg, #f59e0b10, #f59e0b05); border: 1px solid #f59e0b20; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #f59e0b; font-size: 2rem;">{registry_data.get('workforce_stats', {}).get('training', 0)}</div>
                            <div class="metric-label">In Training</div>
                        </div>
                        <div class="metric-item" style="background: linear-gradient(135deg, #8b5cf610, #8b5cf605); border: 1px solid #8b5cf620; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #8b5cf6; font-size: 2rem;">{registry_data.get('workforce_stats', {}).get('planned', 0)}</div>
                            <div class="metric-label">Planned</div>
                        </div>
                        <div class="metric-item" style="background: linear-gradient(135deg, #ec489910, #ec489905); border: 1px solid #ec489920; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #ec4899; font-size: 2rem;">{registry_data.get('workforce_stats', {}).get('executives', 0)}</div>
                            <div class="metric-label">Executives</div>
                        </div>
                    </div>

                    <!-- Development Progress Bar -->
                    <div style="margin-bottom: 2rem;">
                        <h5 style="color: var(--secondary-text); margin-bottom: 0.5rem;">Development Pipeline Progress</h5>
                        <div style="background: var(--border-color); border-radius: 10px; overflow: hidden; height: 30px; position: relative;">
                            {self._generate_pipeline_progress_bar(registry_data.get('workforce_stats', {}))}
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.8rem; color: var(--secondary-text);">
                            <span>Planned</span>
                            <span>In Development</span>
                            <span>Training</span>
                            <span>Testing</span>
                            <span>Operational</span>
                        </div>
                    </div>

                    <!-- Average Metrics -->
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 0.9rem; color: var(--secondary-text); margin-bottom: 0.5rem;">Average Skill Level</div>
                            <div style="font-size: 3rem; font-weight: 600; color: var(--accent-color);">
                                {registry_data.get('workforce_stats', {}).get('avg_skill', '0')}/5
                            </div>
                            <div style="margin-top: 0.5rem;">
                                {self._generate_skill_stars(int(registry_data.get('workforce_stats', {}).get('avg_skill', 0)))}
                            </div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.9rem; color: var(--secondary-text); margin-bottom: 0.5rem;">Average Training Progress</div>
                            <div style="font-size: 3rem; font-weight: 600; color: var(--accent-color);">
                                {registry_data.get('workforce_stats', {}).get('avg_progress', '0')}%
                            </div>
                            <div style="margin-top: 0.5rem;">
                                <div style="width: 200px; height: 10px; background: var(--border-color); border-radius: 5px; margin: 0 auto; overflow: hidden;">
                                    <div style="width: {registry_data.get('workforce_stats', {}).get('avg_progress', '0')}%; height: 100%; background: var(--accent-color); transition: width 0.3s;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
'''

    print(workforce_html)

    print("\n\n📝 Add these helper methods to corporate_headquarters.py:\n")

    helper_methods = '''
    def _generate_pipeline_progress_bar(self, workforce_stats):
        """Generate pipeline progress visualization"""
        total = workforce_stats.get('total', 1)  # Avoid division by zero
        if total == 0:
            return '<div style="text-align: center; padding: 5px;">No workforce data</div>'

        planned_pct = (workforce_stats.get('planned', 0) / total) * 100
        training_pct = (workforce_stats.get('training', 0) / total) * 100
        operational_pct = (workforce_stats.get('operational', 0) / total) * 100
        other_pct = 100 - planned_pct - training_pct - operational_pct

        return f\'\'\'
            <div style="display: flex; height: 100%;">
                <div style="width: {planned_pct}%; background: #8b5cf6;" title="Planned: {workforce_stats.get('planned', 0)}"></div>
                <div style="width: {other_pct}%; background: #ec4899;" title="In Development: {int(workforce_stats.get('total', 0) * other_pct / 100)}"></div>
                <div style="width: {training_pct}%; background: #f59e0b;" title="Training: {workforce_stats.get('training', 0)}"></div>
                <div style="width: {operational_pct}%; background: #10b981;" title="Operational: {workforce_stats.get('operational', 0)}"></div>
            </div>
        \'\'\'

    def _generate_skill_stars(self, level):
        """Generate star rating visualization"""
        stars = ''
        for i in range(5):
            if i < level:
                stars += '<i class="fas fa-star" style="color: #f59e0b;"></i>'
            else:
                stars += '<i class="far fa-star" style="color: var(--border-color);"></i>'
        return stars
'''

    print(helper_methods)

    print("\n\n💡 Implementation steps:")
    print("1. Add the workforce dashboard HTML after Registry Statistics")
    print("2. Add the two helper methods to the class")
    print("3. The registry will now show:")
    print("   - Complete workforce overview with 155 agents")
    print("   - Development pipeline visualization")
    print("   - Average skill level and training progress")
    print("   - Breakdown by operational status")

    print("\n📊 The enhanced registry will display:")
    print("- Total: 195 agents (not just 40)")
    print("- Leaders: 33")
    print("- Workforce: 155")
    print("- Executives: 5")
    print("- Operational agents: 40")
    print("- Agents in training: 45")
    print("- Planned agents: 75")


if __name__ == "__main__":
    generate_workforce_section()
