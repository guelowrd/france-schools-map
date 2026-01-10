// Initialize map centered on Pays de la Loire
const map = L.map('map').setView([47.5, -0.75], 9);

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

// Format IPS value with context
function formatIPS(school) {
    if (!school.ips || !school.ips.value) {
        return '<p><strong>IPS:</strong> Non disponible</p>';
    }

    const ips = parseFloat(school.ips.value);
    const national = school.ips.national_average ? parseFloat(school.ips.national_average) : null;
    const dept = school.ips.departemental_average ? parseFloat(school.ips.departemental_average) : null;

    let html = `<p><strong>IPS:</strong> ${ips.toFixed(1)}`;

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
        html += ` <span class="ips-context">(${comparisons.join(', ')})</span>`;
    }

    html += '</p>';

    // Add diversity indicator
    if (school.ips.ecart_type) {
        const ecartType = parseFloat(school.ips.ecart_type);
        html += `<p style="font-size: 11px; color: #666;"><strong>Diversité:</strong> Écart-type ${ecartType.toFixed(1)} (${ecartType > 35 ? 'élevée' : ecartType > 25 ? 'moyenne' : 'faible'})</p>`;
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
        html += `<p><strong>Brevet ${exam.year}:</strong> ${exam.success_rate.toFixed(1)}% de réussite</p>`;

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
        html += `<p><strong>Bac ${exam.year}:</strong> ${exam.success_rate.toFixed(1)}% de réussite</p>`;

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

    html += '<div class="school-info">';

    // Address
    html += `<p><strong>📍 Adresse:</strong> ${school.address.city} (${school.address.postal_code})</p>`;

    // Student count and class size
    if (school.student_count) {
        html += `<p><strong>👥 Élèves:</strong> ${school.student_count}`;
        if (school.estimated_class_size) {
            html += ` <span style="font-size: 11px; color: #666;">(~${Math.round(school.estimated_class_size)} par classe)</span>`;
        }
        html += '</p>';
    }

    // IPS
    html += formatIPS(school);

    // Exam results
    html += formatExamResults(school);

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

    html += '</div></div>';
    return html;
}

// City search functionality
let allSchools = [];
let cityData = {};

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

// Load and display schools
fetch('data/schools.json')
    .then(response => response.json())
    .then(schools => {
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

        // Create array to hold all markers for bounds calculation
        const allMarkers = [];

        // Add markers for each school directly to the map (no clustering)
        schools.forEach(school => {
            const lat = school.coordinates.latitude;
            const lon = school.coordinates.longitude;

            if (!lat || !lon) return;

            const marker = L.marker([lat, lon], {
                icon: createMarkerIcon(school.type)
            });

            // Bind popup
            marker.bindPopup(createPopupContent(school), {
                maxWidth: 450,
                className: 'school-popup'
            });

            // Bind tooltip (hover)
            marker.bindTooltip(school.name, {
                direction: 'top',
                offset: [0, -6]
            });

            marker.addTo(map);
            allMarkers.push(marker);
        });

        // Fit bounds to show all markers
        if (allMarkers.length > 0) {
            const group = L.featureGroup(allMarkers);
            map.fitBounds(group.getBounds(), { padding: [50, 50] });
        }

        // Initialize search functionality
        initializeSearch(schools);

        console.log('Map loaded successfully');
    })
    .catch(error => {
        console.error('Error loading schools data:', error);
        alert('Erreur lors du chargement des données. Veuillez rafraîchir la page.');
    });
