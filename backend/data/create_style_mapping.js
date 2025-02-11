const fs = require('fs');
const Papa = require('papaparse');
const path = require('path');

async function createStyleMapping() {
    try {
        // Read the input file
        const inputPath = path.join(__dirname, 'SanMar_SDL_N.csv');
        const response = fs.readFileSync(inputPath, 'utf8');
        
        // Parse the CSV data
        const parsedData = Papa.parse(response, {
            delimiter: ',',
            header: false,
            skipEmptyLines: true
        });

        // Create mapping
        const styleMapping = new Map();
        
        // Process each row
        parsedData.data.forEach(row => {
            if (row.length >= 4) {
                const productName = row[1].trim();
                const styleNumber = row[3].trim();
                
                if (productName && styleNumber) {
                    // Remove the style number from the end of the product name if it exists
                    const cleanProductName = productName.replace(new RegExp(`\\s*\\.\\s*${styleNumber}\\s*$`), '');
                    styleMapping.set(styleNumber, cleanProductName);
                }
            }
        });

        // Create CSV content
        const mappingRows = [['Style Number', 'Product Name']];
        Array.from(styleMapping.entries())
            .sort((a, b) => a[0].localeCompare(b[0]))
            .forEach(([style, name]) => {
                mappingRows.push([style, name]);
            });

        // Convert to CSV string
        const csvContent = Papa.unparse(mappingRows);

        // Write the output file
        const outputPath = path.join(__dirname, 'style_to_product_mapping.csv');
        fs.writeFileSync(outputPath, csvContent);
        
        console.log(`Successfully created mapping file: ${outputPath}`);
        console.log(`Total styles mapped: ${styleMapping.size}`);
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// Execute the function
createStyleMapping();