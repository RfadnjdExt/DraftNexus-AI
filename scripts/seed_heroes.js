const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, '../data');
const API_URL = "https://api.gms.moontontech.com/api/gms/source/2669606/2756564";
const HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "gYC6snq+SwW5fqZLrdOzEyXih6s=",
    "content-type": "application/json;charset=UTF-8",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "x-actid": "2669607",
    "x-appid": "2669606",
    "x-lang": "en",
    "Referer": "https://www.mobilelegends.com/"
};

const DETAIL_API_URL = "https://api.gms.moontontech.com/api/gms/source/2669606/2756567";
const DETAIL_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "oPxQMyLOfV+6t1xKEYWuy5VkDC0=",
    "content-type": "application/json;charset=UTF-8",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "x-actid": "2669607",
    "x-appid": "2669606",
    "x-lang": "en",
    "Referer": "https://www.mobilelegends.com/"
};

const GUIDE_API_URL = "https://api.gms.moontontech.com/api/gms/source/2669606/2756564";
const GUIDE_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "0Pw0gKbo/cQkI2akbf+t36hMrZ8=",
    "content-type": "application/json;charset=UTF-8",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "x-actid": "2669607",
    "x-appid": "2669606",
    "x-lang": "en",
    "Referer": "https://www.mobilelegends.com/"
};

const STATS_API_URL = "https://api.gms.moontontech.com/api/gms/source/2669606/2756569";
const STATS_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "gYC6snq+SwW5fqZLrdOzEyXih6s=",
    "content-type": "application/json;charset=UTF-8",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "x-actid": "2669607",
    "x-appid": "2669606",
    "x-lang": "en",
    "Referer": "https://www.mobilelegends.com/"
};

async function fetchHeroStats(heroId, matchType) {
    const body = {
        "pageSize": 20,
        "pageIndex": 1,
        "filters": [
            { "field": "match_type", "operator": "eq", "value": matchType },
            { "field": "main_heroid", "operator": "eq", "value": heroId.toString() },
            { "field": "bigrank", "operator": "eq", "value": 7 }
        ],
        "sorts": []
    };

    try {
        const response = await fetch(STATS_API_URL, {
            method: 'POST',
            headers: STATS_HEADERS,
            body: JSON.stringify(body)
        });
        const json = await response.json();
        return json;
    } catch (error) {
        console.error(`Error fetching stats (type ${matchType}) for hero ${heroId}:`, error);
        return null;
    }
}

async function fetchHeroIcons() {
    console.log("Fetching Hero Icons from Main API...");
    const body = {
        "pageSize": 200,
        "pageIndex": 1,
        "filters": [],
        "sorts": []
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: HEADERS,
            body: JSON.stringify(body)
        });
        const json = await response.json();

        const iconMap = new Map();
        if (json && json.data && json.data.records) {
            json.data.records.forEach(rec => {
                const d = rec.data;
                if (d && d.heroid && d.head) {
                    iconMap.set(d.heroid.toString(), d.head);
                }
            });
        }
        console.log(`Fetched ${iconMap.size} icons.`);
        return iconMap;
    } catch (error) {
        console.error("Error fetching hero icons:", error);
        return new Map();
    }
}

async function main() {
    console.log("Starting Advanced Stats Seeding (Requests 6 & 7)...");

    // Fetch Icons
    const iconMap = await fetchHeroIcons();

    const baseStatsPath = path.join(OUTPUT_DIR, 'hero_base_stats.csv');
    const counterPath = path.join(OUTPUT_DIR, 'hero_counter_stats.csv');
    const compatibilityPath = path.join(OUTPUT_DIR, 'hero_compatibility_stats.csv');

    if (!fs.existsSync(baseStatsPath)) {
        console.error("Error: hero_base_stats.csv not found.");
        console.error("Please run the initial seed script first.");
        return;
    }

    const content = fs.readFileSync(baseStatsPath, 'utf-8');
    const lines = content.trim().split('\n');
    const heroes = [];
    lines.slice(1).forEach(line => {
        const cols = line.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/);
        if (cols.length > 0) heroes.push(cols[0].trim());
    });

    console.log(`Found ${heroes.length} heroes. Fetching Stats...`);

    let counterCSV = "Hero_ID,Strong_Against_JSON,Weak_Against_JSON\n";
    let compatibilityCSV = "Hero_ID,Best_Teammate_JSON,Worst_Teammate_JSON\n";

    for (const heroId of heroes) {
        const counterRes = await fetchHeroStats(heroId, 0);
        let strongAgainst = "[]";
        let weakAgainst = "[]";

        if (counterRes && counterRes.data && counterRes.data.records && counterRes.data.records.length > 0) {
            const record = counterRes.data.records[0];
            if (record && record.data) {
                if (record.data.sub_hero) strongAgainst = JSON.stringify(record.data.sub_hero);
                if (record.data.sub_hero_last) weakAgainst = JSON.stringify(record.data.sub_hero_last);
            }
        }

        const compRes = await fetchHeroStats(heroId, 1);
        let bestTeammate = "[]";
        let worstTeammate = "[]";

        if (compRes && compRes.data && compRes.data.records && compRes.data.records.length > 0) {
            const record = compRes.data.records[0];
            if (record && record.data) {
                if (record.data.sub_hero) bestTeammate = JSON.stringify(record.data.sub_hero);
                if (record.data.sub_hero_last) worstTeammate = JSON.stringify(record.data.sub_hero_last);
            }
        }

        const safeStrong = strongAgainst.replace(/"/g, '""');
        const safeWeak = weakAgainst.replace(/"/g, '""');
        const safeBest = bestTeammate.replace(/"/g, '""');
        const safeWorst = worstTeammate.replace(/"/g, '""');

        counterCSV += `${heroId},"${safeStrong}","${safeWeak}"\n`;
        compatibilityCSV += `${heroId},"${safeBest}","${safeWorst}"\n`;

        if (heroes.indexOf(heroId) % 10 === 0) console.log(`Processed ${heroes.indexOf(heroId)}/${heroes.length} heroes...`);
    }

    if (!fs.existsSync(OUTPUT_DIR)) {
        fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    fs.writeFileSync(counterPath, counterCSV);
    fs.writeFileSync(compatibilityPath, compatibilityCSV);

    console.log("Stats CSVs generated successfully.");

    enhanceBaseStats(iconMap);
}

function enhanceBaseStats(iconMap) {
    console.log("Enhancing hero_base_stats.csv with Advanced Metrics and Icons...");

    const baseStatsPath = path.join(OUTPUT_DIR, 'hero_base_stats.csv');
    const skillsPath = path.join(OUTPUT_DIR, 'hero_skills.csv');
    const metaPath = path.join(OUTPUT_DIR, 'hero_meta_performance.csv');

    if (!fs.existsSync(baseStatsPath) || !fs.existsSync(skillsPath)) {
        console.error("Missing base stats or skills file for enhancement.");
        return;
    }

    const baseContent = fs.readFileSync(baseStatsPath, 'utf-8');
    const skillsContent = fs.readFileSync(skillsPath, 'utf-8');
    let metaContent = "";
    if (fs.existsSync(metaPath)) {
        metaContent = fs.readFileSync(metaPath, 'utf-8');
    }

    const baseLines = baseContent.trim().split('\n');
    const skillLines = skillsContent.trim().split('\n');
    const metaLines = metaContent.trim().split('\n');

    const metaMap = new Map();
    if (metaLines.length > 1) {
        for (let i = 1; i < metaLines.length; i++) {
            const line = metaLines[i];
            const cols = line.split(',');
            if (cols.length < 2) continue;
            const hId = cols[0].trim();
            metaMap.set(hId, {
                Ban_Rate: cols[1],
                Base_Win_Rate: cols[3]
            });
        }
    }

    const heroSkillsMap = new Map();
    for (let i = 1; i < skillLines.length; i++) {
        const line = skillLines[i];
        const cols = line.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/);
        if (cols.length < 2) continue;
        const heroId = cols[0].trim();
        let jsonStr = cols[1].trim();
        if (jsonStr.startsWith('"') && jsonStr.endsWith('"')) {
            jsonStr = jsonStr.substring(1, jsonStr.length - 1);
        }
        jsonStr = jsonStr.replace(/""/g, '"');
        try {
            const skills = JSON.parse(jsonStr);
            heroSkillsMap.set(heroId, skills);
        } catch (e) { }
    }

    let newCsvContent = "Hero_ID,Hero_Name,Primary_Lane,Secondary_Lane,Damage_Type,Scaling_Attribute,Specialty_Burst,Specialty_CC,Specialty_Mobility,Specialty_Guard,Hard_CC_Count,Soft_CC_Count,Attack_Range_Type,Economy_Dependency,Damage_Area_Type,Flex_Pick_Score,Escape_Reliability,Difficulty,Icon_URL\n";

    for (let i = 1; i < baseLines.length; i++) {
        const line = baseLines[i];
        const cols = line.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/);
        if (cols.length < 10) continue;

        const heroId = cols[0].trim();
        const primaryLane = parseInt(cols[2]);
        const secondaryLane = parseInt(cols[3]);
        const basePart = cols.slice(0, 10).join(",");

        const skillsData = heroSkillsMap.get(heroId) || [];
        const metaData = metaMap.get(heroId);

        const stats = calculateStrategicStats(heroId, primaryLane, secondaryLane, skillsData, metaData);

        const iconUrl = iconMap && iconMap.has(heroId) ? iconMap.get(heroId) : "";

        newCsvContent += `${basePart},${stats.hardCC},${stats.softCC},${stats.rangeType},${stats.economy},${stats.aoeType},${stats.flexScore},${stats.escapeReliability},${stats.difficulty},${iconUrl}\n`;
    }

    fs.writeFileSync(baseStatsPath, newCsvContent);
    console.log("hero_base_stats.csv updated with Advanced Metrics.");

    enhanceMetaStats();
}

function enhanceMetaStats() {
    console.log("Enhancing hero_meta_performance.csv with Timestamp...");
    const metaPath = path.join(OUTPUT_DIR, 'hero_meta_performance.csv');

    if (!fs.existsSync(metaPath)) {
        console.error("Meta stats file not found.");
        return;
    }

    const content = fs.readFileSync(metaPath, 'utf-8');
    const lines = content.trim().split('\n');
    let newContent = "";

    const headers = lines[0].split(',');
    if (!headers.includes("Data_Timestamp")) {
        newContent += lines[0].trim() + ",Data_Timestamp\n";
    } else {
        newContent += lines[0].trim() + "\n";
    }

    const today = new Date().toISOString().split('T')[0];

    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        const cols = line.split(',');
        if (cols.length === 8) {
            newContent += line + `,${today}\n`;
        } else {
            const baseCols = cols.slice(0, 8).join(',');
            newContent += baseCols + `,${today}\n`;
        }
    }

    fs.writeFileSync(metaPath, newContent);
    console.log("hero_meta_performance.csv updated.");
}

function calculateStrategicStats(heroId, primaryLane, secondaryLane, skillsData, metaData) {
    let hardCC = 0;
    let softCC = 0;
    let isAOE = false;
    let escapeReliability = 0;

    if (skillsData && skillsData.length > 0 && skillsData[0].skilllist) {
        skillsData[0].skilllist.forEach(skill => {
            const desc = (skill.skilldesc || "").toLowerCase();
            const tags = skill.skilltag || [];

            let hasHard = false;
            let hasSoft = false;

            const isSlowTag = tags.some(t => t.tagid === 22);

            if (desc.includes("stun") || desc.includes("knock up") || desc.includes("knocked airborne") || desc.includes("suppress") || desc.includes("petrify") || desc.includes("taunt") || desc.includes("airborne") || desc.includes("freeze") || desc.includes("transform")) {
                hasHard = true;
            }
            if (desc.includes("slow") || desc.includes("immobilize") || desc.includes("root") || desc.includes("silence")) {
                hasSoft = true;
            }

            if (hasHard) hardCC++;
            else if (hasSoft || isSlowTag) softCC++;

            if (tags.some(t => t.tagid === 32) || desc.includes("area") || desc.includes("multiple enemies")) {
                isAOE = true;
            }

            let skillEscape = 0;
            const isMobilityTag = tags.some(t => t.tagid === 81);
            const isSpeedUpTag = tags.some(t => t.tagid === 61);
            const isTeleportTag = tags.some(t => t.tagid === 82);

            if (desc.includes("untargetable") || desc.includes("immune to control") || desc.includes("remove all debuffs") || desc.includes("purify")) {
                skillEscape = 3;
            } else if (isTeleportTag || desc.includes("blink") || (isMobilityTag && desc.includes("wall"))) {
                skillEscape = 2;
            } else if (isMobilityTag || desc.includes("dash") || desc.includes("jump") || desc.includes("charge")) {
                skillEscape = 2;
            } else if (isSpeedUpTag || desc.includes("movement speed")) {
                skillEscape = 1;
            }

            if (skillEscape > escapeReliability) escapeReliability = skillEscape;
        });
    }

    let rangeType = 1;
    if (primaryLane === 5 || primaryLane === 2) rangeType = 2;

    let economy = 1;
    switch (primaryLane) {
        case 5: economy = 5; break;
        case 4: economy = 4; break;
        case 2: economy = 3; break;
        case 1: economy = 2; break;
        case 3: economy = 1; break;
        default: economy = 3;
    }

    let flexScore = 0;
    if (secondaryLane !== 0) flexScore += 1;

    if (metaData) {
        const banRate = parseFloat(metaData.Ban_Rate || 0);
        const winRate = parseFloat(metaData.Base_Win_Rate || 0);

        if (banRate > 0.4) flexScore += 1;
        else if (banRate > 0.1) flexScore += 0.5;

        if (winRate > 0.52) flexScore += 1;
    }

    let difficulty = 40;
    switch (primaryLane) {
        case 4: difficulty += 30; break;
        case 5: difficulty += 20; break;
        case 2: difficulty += 10; break;
        case 1: difficulty += 0; break;
        case 3: difficulty -= 10; break;
    }
    difficulty += (escapeReliability * 10);

    difficulty = Math.min(100, Math.max(1, difficulty));

    return {
        hardCC,
        softCC,
        rangeType,
        economy,
        aoeType: isAOE ? 2 : 1,
        flexScore,
        escapeReliability,
        difficulty
    };
}

main();
