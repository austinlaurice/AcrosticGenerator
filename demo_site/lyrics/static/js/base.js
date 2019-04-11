// Draw form according to sentence length
var coloredForm = new Array();
function tableCreate(divID){
    coloredForm = new Array();
    var table_div = document.getElementById(divID);
    var tbl = document.createElement('table');
    tbl.classList.add('table');
    tbl.classList.add('table-bordered');
    var tblbody = document.createElement('tbody');
    //var sentence_len_str = document.getElementById('length').value;
    var sentence_len_str = document.getElementById('length').value;
    console.log(sentence_len_str);
    if (sentence_len_str != ''){
        var sentence_len = sentence_len_str.split(';');
        for (var j=0; j<sentence_len.length; j++){
            // generate form according to the conditions
            // need to have row & col index for each slot
            var row = document.createElement('tr');

            for (var i=0; i<sentence_len[j]; i++) {
                // create element <td> and text node
                // Make text node the contents of <td> element
                // put <td> at end of the table row
                var cell = document.createElement("td");
                //cell.onclick = changeSlotColor(this);
                //var cellText = document.createTextNode("cell is row " + j + ", column " + i);
                var cell_count = '';
                if (i<9){
                    cell_count = '0' + (i+1);
                }
                else{
                    cell_count = i+1;
                }
                //var cellText = document.createTextNode(j + ',' + i);
                var cellText = document.createTextNode(cell_count);

                //cell.value = j + '_' + i;
                cell.appendChild(cellText);
                row.appendChild(cell);
            }

            //row added to end of table body
            tblbody.appendChild(row);
        }

        // append the <tbody> inside the <table>
        tbl.appendChild(tblbody);
        // put <table> in the <body>
        table_div.appendChild(tbl);
        // tbl border attribute to 
    }
    else{
    // generate 6 * 15 slots (?) if not said
        for (var j=0; j<6; j++){
            // generate form according to the conditions
            // need to have row & col index for each slot
            var row = document.createElement('tr');

            for (var i=0; i<15; i++) {
                // create element <td> and text node
                // Make text node the contents of <td> element
                // put <td> at end of the table row
                var cell = document.createElement("td");
                //cell.onclick = changeSlotColor(this);
                //var cellText = document.createTextNode('( ' + j + ' , ' + i + ' )');
                var cell_count = ''
                if (i<9){
                    cell_count = '0' + (i+1);
                }
                else{
                    cell_count = i+1;
                }

                //var cellText = document.createTextNode(j + ',' + i);
                var cellText = document.createTextNode(cell_count);

                cell.appendChild(cellText);
                row.appendChild(cell);
            }

            //row added to end of table body
            tblbody.appendChild(row);
        }

        // append the <tbody> inside the <table>
        tbl.appendChild(tblbody);
        // put <table> in the <body>
        table_div.appendChild(tbl);
    }
    //tbl.setAttribute("border", "2");
    //tbl.setAttribute("width", "100%");
    //table_div.setAttribute("table-layout", "fixed");
}

// Draw the table when "Draw it myself" is selected
function tableShow(divID, element){
    if (element.value == 3){
        tableCreate(divID);
    }
    else{
        var clearElement = document.getElementById(divID);
        clearElement.innerHTML = '';
        coloredForm = new Array();
        var update_index = document.getElementById('selected_index');
        update_index.value='';
    }
    changeSlotColor();
}

// Change color and value when clicked and save the index of changed ones in an array
function changeSlotColor(){
    [].forEach.call(document.getElementsByTagName('td'), function(item){
        item.addEventListener('click', function(){
            // already colored
            var row = item.parentElement.rowIndex;
            var col = item.cellIndex;
            var new_index = row + '_' + col;
            console.log(row + ',' + col);
            if (item.style.backgroundColor == 'rgb(170, 170, 170)'){
                item.style.backgroundColor = '#FFFFFF';
                coloredForm.splice(coloredForm.indexOf(new_index), 1);
                //console.log(item.rowIndex);
            }
            else{
                item.style.backgroundColor = '#AAAAAA';
                coloredForm.push(new_index);
            }
            var update_index = document.getElementById('selected_index');
            var indexes = Array.from(coloredForm).join(' ');
            update_index.value = indexes;
            console.log(indexes);
        }, false);
    });
}
