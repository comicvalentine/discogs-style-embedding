const plot = document.querySelector('.js-plotly-plot');

// 1. control bar
const controlBar = document.createElement('div');
controlBar.style = `
    position: absolute; 
    top: 0px; 
    left: 20px; 
    z-index: 1000; 
    display: flex; 
    gap: 20px; 
    align-items: flex-start; 
    padding: 15px; 
    font-family: 'Inter', -apple-system, sans-serif;
`;
plot.parentNode.insertBefore(controlBar, plot);

const createGroup = (label, content) => {
    const group = document.createElement('div');
    group.style = "display: flex; flex-direction: column; gap: 8px;";
    const labelSpan = document.createElement('span');
    labelSpan.innerText = label;
    labelSpan.style = "font-weight: bold; font-size: 14px; color: #333;";
    group.appendChild(labelSpan);
    group.appendChild(content);
    return group;
};

// 2. Text Toggle (Show/Hide)
const textGroupWrapper = document.createElement('div');
textGroupWrapper.style = "display: flex; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);";

const showBtn = document.createElement('button');
showBtn.innerText = "show";
showBtn.style = "padding: 8px 16px; border: none; cursor: pointer; background: #18D85F; color: white; font-weight: 500;";

const hideBtn = document.createElement('button');
hideBtn.innerText = "hide";
hideBtn.style = "padding: 8px 16px; border: none; cursor: pointer; background: #e0e0e0; color: #666;";

showBtn.onclick = () => {
    showBtn.style.background = "#18D85F"; showBtn.style.color = "white";
    hideBtn.style.background = "#e0e0e0"; hideBtn.style.color = "#666";
    Plotly.restyle(plot, {mode: 'markers+text'});
};
hideBtn.onclick = () => {
    hideBtn.style.background = "#18D85F"; hideBtn.style.color = "white";
    showBtn.style.background = "#e0e0e0"; showBtn.style.color = "#666";
    Plotly.restyle(plot, {mode: 'markers'});
};

textGroupWrapper.appendChild(showBtn);
textGroupWrapper.appendChild(hideBtn);
controlBar.appendChild(createGroup("Text", textGroupWrapper));

// 3. Mode Toggle (Move/Focus)
const modeGroupWrapper = document.createElement('div');
modeGroupWrapper.style = "display: flex; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);";

const moveBtn = document.createElement('button');
moveBtn.innerHTML = "✢ move";
moveBtn.style = "padding: 8px 16px; border: none; cursor: pointer; background: #1393FD; color: white;";

const focusBtn = document.createElement('button');
focusBtn.innerHTML = "⛶ focus";
focusBtn.style = "padding: 8px 16px; border: none; cursor: pointer; background:  #e0e0e0; color: #666;";

focusBtn.onclick = () => {
    focusBtn.style.background = "#1393FD"; focusBtn.style.color = "white";
    moveBtn.style.background = "#e0e0e0"; moveBtn.style.color = "#666";
    Plotly.relayout(plot, {dragmode: 'zoom'});
};
moveBtn.onclick = () => {
    moveBtn.style.background = "#1393FD"; moveBtn.style.color = "white";
    focusBtn.style.background = "#e0e0e0"; focusBtn.style.color = "#666";
    Plotly.relayout(plot, {dragmode: 'pan'});
};

modeGroupWrapper.appendChild(moveBtn);
modeGroupWrapper.appendChild(focusBtn);
controlBar.appendChild(createGroup("Mode", modeGroupWrapper));

// 3. Zoom Controller ( - 100% + )
const zoomGroupWrapper = document.createElement('div');
zoomGroupWrapper.style = "display: flex; align-items: center; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); background: white;";

const handleZoom = (factor) => {
    const xr = plot._fullLayout.xaxis.range;
    const yr = plot._fullLayout.yaxis.range;
    
    const currentXSpan = xr[1] - xr[0];
    const currentYSpan = yr[1] - yr[0];
    const centerX = (xr[0] + xr[1]) / 2;
    const centerY = (yr[0] + yr[1]) / 2;

    const newHalfX = (currentXSpan * factor) / 2;
    const newHalfY = (currentYSpan * factor) / 2;

    Plotly.relayout(plot, {
        'xaxis.range': [centerX - newHalfX, centerX + newHalfX],
        'yaxis.range': [centerY - newHalfY, centerY + newHalfY],
        'xaxis.autorange': false,
        'yaxis.autorange': false
    });
};

const minusBtn = document.createElement('button');
minusBtn.innerText = "-";
minusBtn.style = "padding: 8px 12px; border: none; cursor: pointer; background: #e0e0e0; font-weight: bold;";
minusBtn.onclick = () => handleZoom(1.25); 

const zoomIcon = document.createElement('div');
zoomIcon.innerHTML = "🔍";
zoomIcon.style = "padding: 0 10px; font-size: 14px;";

const plusBtn = document.createElement('button');
plusBtn.innerText = "+";
plusBtn.style = "padding: 8px 12px; border: none; cursor: pointer; background: #e0e0e0; font-weight: bold;";

plusBtn.onclick = () => handleZoom(0.8); 

zoomGroupWrapper.appendChild(minusBtn);
zoomGroupWrapper.appendChild(zoomIcon);
zoomGroupWrapper.appendChild(plusBtn);
controlBar.appendChild(createGroup("Zoom", zoomGroupWrapper));


// 4. Search Style
const searchInput = document.createElement('input');
searchInput.placeholder = "Style (e.g. Dance Pop)";
searchInput.style = "padding: 10px 15px; border: 1px solid #ccc; border-radius: 20px; width: 180px; outline: none;";

const showSearchMessage = (message, color) => {
    const msgBox = document.createElement('div');
    msgBox.innerText = message;
    Object.assign(msgBox.style, {
        position: 'absolute',
        top: '65px',
        left: '0',
        background: color,
        color: 'white',
        padding: '5px 12px',
        borderRadius: '15px',
        fontSize: '12px',
        fontWeight: 'bold',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        zIndex: '1001',
        transition: 'opacity 0.5s ease',
        whiteSpace: 'nowrap'
    });
    
    searchInput.parentElement.style.position = 'relative';
    searchInput.parentElement.appendChild(msgBox);

    setTimeout(() => {
        msgBox.style.opacity = '0';
        setTimeout(() => msgBox.remove(), 500);
    }, 2000);
};

searchInput.onkeypress = (e) => {
    if (e.key === 'Enter') {
        const term = searchInput.value.toLowerCase().replace(/[-_]/g, ' ').replace(/\s+/g, ' ').trim();
        if (!term) return;

        const matches = search_data.filter(row => {
            const cleanStyle = (row.style || "").toLowerCase().replace(/[-_]/g, ' ').replace(/\s+/g, ' ');
            return cleanStyle.includes(term);
        });
        console.log(matches[0]) 
        if (matches.length > 0) {
            const sumX = matches.reduce((acc, curr) => acc + Number(curr.dim_0), 0);
            const sumY = matches.reduce((acc, curr) => acc + Number(curr.dim_1), 0);
            
            const avgX = sumX / matches.length;
            const avgY = sumY / matches.length;

            const allX = search_data.map(d => Number(d.dim_0));
            const allY = search_data.map(d => Number(d.dim_1));
            
            const globalMinX = Math.min(...allX);
            const globalMaxX = Math.max(...allX);
            const globalMinY = Math.min(...allY);
            const globalMaxY = Math.max(...allY);

            const globalSpanX = globalMaxX - globalMinX;
            const globalSpanY = globalMaxY - globalMinY;

            const zoomRatio = 0.15; 
            const halfSpanX = (globalSpanX * zoomRatio) / 2;
            const halfSpanY = (globalSpanY * zoomRatio) / 2;

            Plotly.relayout(plot, {
                'xaxis.autorange': false,
                'yaxis.autorange': false,
                'xaxis.range': [avgX - halfSpanX, avgX + halfSpanX],
                'yaxis.range': [avgY - halfSpanY, avgY + halfSpanY]
            });
            searchInput.style.borderColor = "#18D85F";
            setTimeout(() => searchInput.style.borderColor = "#ccc", 1000);
        } else {
            searchInput.style.borderColor = "#FB2E46";
            setTimeout(() => searchInput.style.borderColor = "#ccc", 1000);
            showSearchMessage(`"${searchInput.value}" is not found`, '#FB2E46');
        }
    }
};
controlBar.appendChild(createGroup("Search", searchInput));

// 6. Reset View
const resetBtn = document.createElement('button');
resetBtn.innerText = "Reset View";
resetBtn.style = "margin-top: 25px; padding: 10px 20px; cursor: pointer; background: #FB2E46; color: white; border: none; border-radius: 4px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: 0.2s;";
resetBtn.onmouseover = () => resetBtn.style.background = "#ff6b81";
resetBtn.onmouseout = () => resetBtn.style.background = "#FB2E46";
resetBtn.onclick = () => {
    Plotly.relayout(plot, {'xaxis.autorange': true, 'yaxis.autorange': true});
};
controlBar.appendChild(resetBtn);
