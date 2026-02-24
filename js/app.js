// Skills Data
const skillsData = [
    {
        id: "exam-creator",
        comingSoon: true,
        title: "Multiple Choice Exam Creator",
        description: "Generates a comprehensive multiple-choice exam based on provided course materials. Includes answer keys and explanations.",
        category: "assessment",
        tags: ["Education", "Testing"],
        file: "skills/exam-creator.zip",
        date: "2025-10-15"
    },
    {
        id: "traditional-syllabus",
        title: "Traditional Law Syllabus Generator",
        description: "Creates a classic law school syllabus structure, including casebook assignments, statutory readings, and Socratic method prompts.",
        category: "syllabus",
        tags: ["Remote Data", "Legal Ed", "Curriculum"],
        file: "skills/syllabus-traditional.skill",
        date: "2025-11-02"
    },
    {
        id: "modern-syllabus",
        title: "Evidence-Based Syllabus Creator",
        description: "Designs a modern syllabus incorporating active learning strategies, formative assessments, and diverse resource types.",
        category: "syllabus",
        tags: ["Remote Data", "Legal Ed", "Curriculum"],
        file: "skills/syllabus-evidence-based.skill",
        date: "2025-12-01"
    }
];

// DOM Elements
const skillsGrid = document.getElementById('skills-grid');
const filterBtns = document.querySelectorAll('.filter-btn');

// Render Skills
function renderSkills(skills) {
    skillsGrid.innerHTML = '';
    
    if (skills.length === 0) {
        skillsGrid.innerHTML = '<p class="no-results">No skills found for this category.</p>';
        return;
    }

    skills.forEach(skill => {
        const card = document.createElement('div');
        card.className = 'skill-card';
        card.setAttribute('data-category', skill.category);
        
        // Generate Tags HTML
        const tagsHtml = skill.tags.map(tag => `<span class="tag">${tag}</span>`).join('');
        
        // Handle Coming Soon state
        const isComingSoon = skill.comingSoon === true;
        const downloadBtn = isComingSoon 
            ? `<span class="download-btn btn-disabled">Coming Soon</span>`
            : `<a href="${skill.file}" class="download-btn" download>Download Skill (.zip)</a>`;
            
        const comingSoonBadge = isComingSoon
            ? `<span class="badge-coming-soon">Coming Soon</span>`
            : '';
        
        card.innerHTML = `
            <div class="skill-header">
                <div class="skill-badges">
                    <span class="skill-category">${skill.category}</span>
                    ${comingSoonBadge}
                </div>
                <span class="skill-date">${skill.date}</span>
            </div>
            <h3 class="skill-title">${skill.title}</h3>
            <p class="skill-desc">${skill.description}</p>
            <div class="skill-meta">
                ${tagsHtml}
            </div>
            ${downloadBtn}
        `;
        
        skillsGrid.appendChild(card);
    });
}

// Filter Functionality
function filterSkills(category) {
    if (category === 'all') {
        renderSkills(skillsData);
    } else {
        const filtered = skillsData.filter(skill => skill.category === category);
        renderSkills(filtered);
    }
}

// Event Listeners
filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all
        filterBtns.forEach(b => b.classList.remove('active'));
        // Add active class to clicked
        btn.classList.add('active');
        
        const filterValue = btn.getAttribute('data-filter');
        filterSkills(filterValue);
    });
});

// Initial Render
document.addEventListener('DOMContentLoaded', () => {
    renderSkills(skillsData);
});
