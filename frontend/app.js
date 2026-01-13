// Initialize map centered between Pays de la Loire and Charente-Maritime
const map = L.map('map').setView([46.5, -0.6], 8);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
}).addTo(map);

// Define marker colors by school type
const markerColors = {
    'Primaire': '#3b82f6',   // Blue
    'Collège': '#eab308',    // Yellow
    'Lycée': '#dc2626'       // Red
};

// Create custom marker icon function
function createMarkerIcon(schoolType) {
    const color = markerColors[schoolType] || '#6b7280';
    return L.divIcon({
        className: 'custom-marker',
        html: `<div style="
            background-color: ${color};
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 0 4px rgba(0,0,0,0.4);
        "></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
    });
}

// Political data (loaded below with schools)
let politicalData = {};

// Format political context
function formatPoliticalContext(school) {
    const inseeCode = school.address?.insee_code;

    if (!inseeCode || !politicalData[inseeCode]) {
        return '<p><em>Données non disponibles</em></p>';
    }

    const pol = politicalData[inseeCode];
    let html = '<div class="political-info">';

    // Line 1: Current Mayor
    if (pol.mayor) {
        const mayorName = `${pol.mayor.first_name} ${pol.mayor.last_name}`;
        const party = pol.mayor.party || 'N/A';
        html += `<p><strong>Maire:</strong> ${mayorName} (${party})</p>`;
    } else {
        html += '<p><strong>Maire:</strong> N/A</p>';
    }

    // Line 2: Municipal 2020
    if (pol.municipal_2020?.percentage) {
        const pct = pol.municipal_2020.percentage.toFixed(1);
        html += `<p><strong>Municipal 2020:</strong> Élu au 2nd tour avec ${pct}% des voix</p>`;
    } else {
        html += '<p><strong>Municipal 2020:</strong> N/A</p>';
    }

    // Line 3: Presidential 2022 - Round 2
    if (pol.presidential_2022?.round_2) {
        const macron = pol.presidential_2022.round_2.macron.toFixed(1);
        const lepen = pol.presidential_2022.round_2.le_pen.toFixed(1);
        html += `<p><strong>Présidentielle 2022 (2nd tour):</strong> ${macron}% Macron, ${lepen}% Le Pen</p>`;
    } else {
        html += '<p><strong>Présidentielle 2022 (2nd tour):</strong> N/A</p>';
    }

    // Line 4: Presidential 2022 - Round 1 (TOP 4)
    if (pol.presidential_2022?.round_1 && pol.presidential_2022.round_1.length > 0) {
        const top4 = pol.presidential_2022.round_1.slice(0, 4)
            .map(c => `${c.percentage.toFixed(1)}% ${c.candidate}`)
            .join(', ');
        html += `<p><strong>Présidentielle 2022 (1er tour):</strong> ${top4}</p>`;
    } else {
        html += '<p><strong>Présidentielle 2022 (1er tour):</strong> N/A</p>';
    }

    // Line 5: Legislative 2024 - Round 2 (TOP 4)
    if (pol.legislative_2024?.round_2 && pol.legislative_2024.round_2.length > 0) {
        const top4 = pol.legislative_2024.round_2.slice(0, 4)
            .map(c => `${c.percentage.toFixed(1)}% ${c.candidate} (${c.party})`)
            .join(', ');
        html += `<p><strong>Législatives 2024 (2nd tour):</strong> ${top4}</p>`;
    } else {
        html += '<p><strong>Législatives 2024 (2nd tour):</strong> N/A</p>';
    }

    // Line 6: Legislative 2024 - Round 1 (TOP 4)
    if (pol.legislative_2024?.round_1 && pol.legislative_2024.round_1.length > 0) {
        const top4 = pol.legislative_2024.round_1.slice(0, 4)
            .map(c => `${c.percentage.toFixed(1)}% ${c.candidate} (${c.party})`)
            .join(', ');
        html += `<p><strong>Législatives 2024 (1er tour):</strong> ${top4}</p>`;
    } else {
        html += '<p><strong>Législatives 2024 (1er tour):</strong> N/A</p>';
    }

    html += '</div>';
    return html;
}

// Format IPS value with context
function formatIPS(school) {
    if (!school.ips || !school.ips.value) {
        return '<p><strong>IPS:</strong> Non disponible</p>';
    }

    const ips = parseFloat(school.ips.value);
    const national = school.ips.national_average ? parseFloat(school.ips.national_average) : null;
    const dept = school.ips.departemental_average ? parseFloat(school.ips.departemental_average) : null;
    const year = school.ips.year || '';

    let html = `<p><strong>IPS:</strong> ${ips.toFixed(1)}`;

    // Add year
    if (year) {
        html += ` <span style="font-size: 10px; color: #999;">(${year})</span>`;
    }

    // Add context
    const comparisons = [];
    if (national) {
        const diff = ips - national;
        comparisons.push(`national: ${diff > 0 ? '+' : ''}${diff.toFixed(1)}`);
    }
    if (dept) {
        const diff = ips - dept;
        comparisons.push(`département: ${diff > 0 ? '+' : ''}${diff.toFixed(1)}`);
    }

    if (comparisons.length > 0) {
        html += `<br><span class="ips-context" style="font-size: 11px;">${comparisons.join(', ')}</span>`;
    }

    html += '</p>';

    // Add diversity indicator (std deviation)
    if (school.ips.ecart_type) {
        const ecartType = parseFloat(school.ips.ecart_type);
        let interpretation = '';
        if (ecartType > 35) {
            interpretation = 'très hétérogène';
        } else if (ecartType >= 28) {
            interpretation = 'plutôt hétérogène';
        } else if (ecartType >= 20) {
            interpretation = 'plutôt homogène';
        } else {
            interpretation = 'très homogène';
        }

        html += `<p style="font-size: 11px; color: #666;"><strong>Diversité sociale:</strong> écart-type ${ecartType.toFixed(1)} (${interpretation})</p>`;
    }

    return html;
}

// Format exam results
function formatExamResults(school) {
    if (!school.exam_results) {
        return '';
    }

    const exam = school.exam_results;
    let html = '<h4>📊 Résultats aux examens</h4>';

    if (exam.type === 'Brevet') {
        html += `<p><strong>Brevet:</strong> ${exam.success_rate.toFixed(1)}% de réussite`;
        if (exam.year) {
            html += ` <span style="font-size: 10px; color: #999;">(${exam.year})</span>`;
        }
        html += '</p>';

        if (exam.students_admitted && exam.students_registered) {
            html += `<p style="font-size: 11px;">${exam.students_admitted} admis sur ${exam.students_registered} inscrits</p>`;
        }

        // Mentions distribution
        if (exam.mentions) {
            const mentions = exam.mentions;
            const total = mentions.sans_mention + mentions.assez_bien + mentions.bien + mentions.tres_bien;
            if (total > 0) {
                const tbPct = (mentions.tres_bien / total * 100).toFixed(0);
                const bPct = (mentions.bien / total * 100).toFixed(0);
                html += `<p style="font-size: 11px;">Mentions: ${tbPct}% TB, ${bPct}% B</p>`;
            }
        }
    } else if (exam.type === 'Baccalauréat') {
        html += `<p><strong>Bac:</strong> ${exam.success_rate.toFixed(1)}% de réussite`;
        if (exam.year) {
            html += ` <span style="font-size: 10px; color: #999;">(${exam.year})</span>`;
        }
        html += '</p>';

        // Access rates - KEY METRIC for student well-being!
        if (exam.access_rate_2nde) {
            html += '<div class="highlight-metric">';
            html += `<p style="margin:0;"><strong>Taux d'accès 2nde → Bac: ${exam.access_rate_2nde}%</strong></p>`;
            html += '<p style="margin:0; font-size: 10px; color: #666;">Élèves qui terminent leur parcours</p>';
            html += '</div>';
        }

        // Value added (how school performs vs expected)
        if (exam.value_added_success !== null && exam.value_added_success !== undefined) {
            const va = exam.value_added_success;
            html += `<p style="font-size: 11px;"><strong>Valeur ajoutée:</strong> ${va > 0 ? '+' : ''}${va} ${va > 0 ? '(mieux qu\'attendu)' : va < 0 ? '(moins bien qu\'attendu)' : '(conforme)'}</p>`;
        }

        if (exam.students_present) {
            html += `<p style="font-size: 11px;">${exam.students_present} candidats présents</p>`;
        }
    }

    return html;
}

// Create popup content for a school
function createPopupContent(school) {
    let html = '<div class="popup-content">';

    // School name and type
    html += `<h3>${school.name}</h3>`;

    // Badges for type and public/private
    html += '<div style="margin-bottom: 8px;">';
    if (school.public_private === 'Public') {
        html += '<span class="badge badge-public">Public</span>';
    } else {
        html += '<span class="badge badge-prive">Privé</span>';
    }
    html += `<span class="badge">${school.type}</span>`;
    html += '</div>';

    // === SECTION 1: Infos École (expandable) ===
    html += '<details class="popup-section" open>';
    html += '<summary>🚸 Infos École</summary>';
    html += '<div class="school-info">';

    // Address
    html += `<p><strong>📍 Adresse:</strong> ${school.address.city} (${school.address.postal_code})</p>`;

    // Student count and class size
    if (school.student_count) {
        html += `<p><strong>👥 Élèves:</strong> ${school.student_count}`;

        // For primary schools, show actual class count and size
        if (school.type === 'Primaire' && school.number_of_classes) {
            html += ` • ${school.number_of_classes} classe${school.number_of_classes > 1 ? 's' : ''}`;
            if (school.class_size) {
                html += ` <span style="font-size: 11px; color: #666;">(${school.class_size} élèves/classe)</span>`;
            }
        }

        // Add enrollment year
        if (school.enrollment_year) {
            html += ` <span style="font-size: 10px; color: #999;">(${school.enrollment_year})</span>`;
        }
        html += '</p>';
    }

    // IPS
    html += formatIPS(school);

    // Exam results
    html += formatExamResults(school);

    // Languages (for collèges and lycées)
    if (school.languages && (school.type === 'Collège' || school.type === 'Lycée')) {
        html += '<h4>🌍 Langues enseignées</h4>';

        if (school.languages.lv1 && school.languages.lv1.length > 0) {
            html += `<p style="font-size: 11px;"><strong>LV1:</strong> ${school.languages.lv1.join(', ')}</p>`;
        }

        if (school.languages.lv2 && school.languages.lv2.length > 0) {
            html += `<p style="font-size: 11px;"><strong>LV2:</strong> ${school.languages.lv2.join(', ')}</p>`;
        }
    }

    // Contact info
    if (school.contact.website || school.contact.phone) {
        html += '<h4>📞 Contact</h4>';
        if (school.contact.phone) {
            html += `<p style="font-size: 11px;">${school.contact.phone}</p>`;
        }
        if (school.contact.website) {
            html += `<p style="font-size: 11px;"><a href="${school.contact.website}" target="_blank">Site web</a></p>`;
        }
    }

    html += '</div></details>';

    // === SECTION 2: Contexte Politique (expandable) ===
    html += '<details class="popup-section">';
    html += '<summary>🏛️ Contexte Politique</summary>';
    html += formatPoliticalContext(school);
    html += '</details>';

    html += '</div>';
    return html;
}

// City search functionality
let allSchools = [];
let cityData = {};
let schoolMarkers = []; // Store all markers with their school data

function initializeSearch(schools) {
    // Build city data with coordinates and school counts
    cityData = {};
    schools.forEach(school => {
        const city = school.address.city;
        if (!cityData[city]) {
            cityData[city] = {
                name: city,
                department: school.address.department,
                coordinates: [],
                schoolCount: 0,
                types: { 'Primaire': 0, 'Collège': 0, 'Lycée': 0 }
            };
        }
        cityData[city].coordinates.push([school.coordinates.latitude, school.coordinates.longitude]);
        cityData[city].schoolCount++;
        cityData[city].types[school.type]++;
    });

    // Set up search input
    const searchInput = document.getElementById('city-search');
    const searchResults = document.getElementById('search-results');

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim().toLowerCase();

        if (query.length < 2) {
            searchResults.classList.remove('active');
            return;
        }

        // Filter cities
        const matches = Object.values(cityData)
            .filter(city => city.name.toLowerCase().includes(query))
            .sort((a, b) => a.name.localeCompare(b.name))
            .slice(0, 10);

        if (matches.length === 0) {
            searchResults.classList.remove('active');
            return;
        }

        // Display results
        searchResults.innerHTML = matches.map(city => `
            <div class="search-result-item" data-city="${city.name}">
                <div class="search-result-city">${city.name}</div>
                <div class="search-result-info">
                    ${city.department} • ${city.schoolCount} établissement${city.schoolCount > 1 ? 's' : ''}
                    (${city.types['Primaire']} primaires, ${city.types['Collège']} collèges, ${city.types['Lycée']} lycées)
                </div>
            </div>
        `).join('');

        searchResults.classList.add('active');

        // Add click handlers to results
        searchResults.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const cityName = item.dataset.city;
                zoomToCity(cityName);
                searchInput.value = cityName;
                searchResults.classList.remove('active');
            });
        });
    });

    // Close results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.remove('active');
        }
    });
}

function zoomToCity(cityName) {
    const city = cityData[cityName];
    if (!city) return;

    // Calculate bounds of all schools in this city
    const bounds = L.latLngBounds(city.coordinates);

    // Zoom to city with padding
    map.fitBounds(bounds, {
        padding: [50, 50],
        maxZoom: 14
    });
}

// Filter functionality
function initializeFilters() {
    const filterPrimaire = document.getElementById('filter-primaire');
    const filterCollege = document.getElementById('filter-college');
    const filterLycee = document.getElementById('filter-lycee');
    const filterPublic = document.getElementById('filter-public');
    const filterPrive = document.getElementById('filter-prive');
    const filterLanguage = document.getElementById('filter-language');

    // Populate language dropdown with all unique languages
    const allLanguages = new Set();
    allSchools.forEach(school => {
        if (school.languages && school.languages.all) {
            school.languages.all.forEach(lang => allLanguages.add(lang));
        }
    });

    // Sort languages alphabetically
    const sortedLanguages = Array.from(allLanguages).sort((a, b) => a.localeCompare(b, 'fr'));

    // Add options to dropdown
    sortedLanguages.forEach(lang => {
        const option = document.createElement('option');
        option.value = lang;
        option.textContent = lang;
        filterLanguage.appendChild(option);
    });

    // Apply filters function
    function applyFilters() {
        const filters = {
            primaire: filterPrimaire.checked,
            college: filterCollege.checked,
            lycee: filterLycee.checked,
            public: filterPublic.checked,
            prive: filterPrive.checked,
            language: filterLanguage.value
        };

        let visibleCount = 0;
        let primaireCount = 0;
        let collegeCount = 0;
        let lyceeCount = 0;

        schoolMarkers.forEach(item => {
            const school = item.school;
            let shouldShow = true;

            // Filter by type
            if (school.type === 'Primaire' && !filters.primaire) shouldShow = false;
            if (school.type === 'Collège' && !filters.college) shouldShow = false;
            if (school.type === 'Lycée' && !filters.lycee) shouldShow = false;

            // Filter by public/private
            if (school.public_private === 'Public' && !filters.public) shouldShow = false;
            if (school.public_private === 'Privé' && !filters.prive) shouldShow = false;

            // Filter by language (only apply if a language is selected)
            if (filters.language && school.languages && school.languages.all) {
                if (!school.languages.all.includes(filters.language)) {
                    shouldShow = false;
                }
            } else if (filters.language && !school.languages) {
                // If language filter is active but school has no language data, hide it
                shouldShow = false;
            }

            // Show/hide marker
            if (shouldShow) {
                if (!map.hasLayer(item.marker)) {
                    item.marker.addTo(map);
                }
                visibleCount++;
                if (school.type === 'Primaire') primaireCount++;
                if (school.type === 'Collège') collegeCount++;
                if (school.type === 'Lycée') lyceeCount++;
            } else {
                if (map.hasLayer(item.marker)) {
                    map.removeLayer(item.marker);
                }
            }
        });

        // Update stats
        document.getElementById('total-schools').textContent = visibleCount;
        document.getElementById('primaire-count').textContent = primaireCount;
        document.getElementById('college-count').textContent = collegeCount;
        document.getElementById('lycee-count').textContent = lyceeCount;
    }

    // Add event listeners
    filterPrimaire.addEventListener('change', applyFilters);
    filterCollege.addEventListener('change', applyFilters);
    filterLycee.addEventListener('change', applyFilters);
    filterPublic.addEventListener('change', applyFilters);
    filterPrive.addEventListener('change', applyFilters);
    filterLanguage.addEventListener('change', applyFilters);
}

// Load both political data and schools data
Promise.all([
    fetch('data/schools.json').then(response => response.json()),
    fetch('data/political_data.json').then(response => response.json())
])
.then(([schools, polData]) => {
    // Store political data
    politicalData = polData;
    console.log(`Loaded political data for ${Object.keys(politicalData).length} communes`);

    // Store schools data
    allSchools = schools;
    console.log(`Loaded ${schools.length} schools`);

        // Update stats
        const primaireCount = schools.filter(s => s.type === 'Primaire').length;
        const collegeCount = schools.filter(s => s.type === 'Collège').length;
        const lyceeCount = schools.filter(s => s.type === 'Lycée').length;

        document.getElementById('total-schools').textContent = schools.length;
        document.getElementById('primaire-count').textContent = primaireCount;
        document.getElementById('college-count').textContent = collegeCount;
        document.getElementById('lycee-count').textContent = lyceeCount;

        // Sort schools so lycées are drawn last (on top)
        // Order: Primaire (bottom), Collège (middle), Lycée (top)
        const schoolOrder = { 'Primaire': 1, 'Collège': 2, 'Lycée': 3 };
        const sortedSchools = [...schools].sort((a, b) => {
            return schoolOrder[a.type] - schoolOrder[b.type];
        });

        // Create markers for all schools (but don't add to map yet)
        sortedSchools.forEach(school => {
            const lat = school.coordinates.latitude;
            const lon = school.coordinates.longitude;

            if (!lat || !lon) return;

            const marker = L.marker([lat, lon], {
                icon: createMarkerIcon(school.type)
            });

            // Bind popup (use function for dynamic content generation)
            marker.bindPopup(() => createPopupContent(school), {
                maxWidth: 450,
                className: 'school-popup'
            });

            // Bind tooltip (hover)
            marker.bindTooltip(school.name, {
                direction: 'top',
                offset: [0, -6]
            });

            // Store marker with school data
            schoolMarkers.push({
                marker: marker,
                school: school
            });
        });

        // Add all markers to map initially
        schoolMarkers.forEach(item => item.marker.addTo(map));

        // Fit bounds to show all markers
        if (schoolMarkers.length > 0) {
            const allMarkers = schoolMarkers.map(item => item.marker);
            const group = L.featureGroup(allMarkers);
            map.fitBounds(group.getBounds(), { padding: [50, 50] });
        }

        // Initialize search functionality
        initializeSearch(schools);

        // Initialize filters
        initializeFilters();

        console.log('Map loaded successfully');
    })
    .catch(error => {
        console.error('Failed to load data:', error);
        alert('Erreur de chargement des données. Veuillez actualiser la page.');
    });
