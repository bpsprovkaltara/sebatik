import fs from 'node:fs/promises'
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool'

const source='C:/Users/user/Downloads/Pemetaan_Indikator_Sumber_Data_ISV_IUP_Kaltara.xlsx'
const input=await FileBlob.load(source)
const workbook=await SpreadsheetFile.importXlsx(input)
const overview=await workbook.inspect({
  kind:'workbook,sheet,table',
  maxChars:12000,
  tableMaxRows:12,
  tableMaxCols:18,
  tableMaxCellChars:160,
})
console.log(overview.ndjson)

const sheetName='Pemetaan Sumber Data'
const sheet=workbook.worksheets.getItem(sheetName)
const values=sheet.getRange('A1:B87').values
await fs.writeFile('.codex-spreadsheet-read/source_rows.json',JSON.stringify(values,null,2),'utf8')
const preview=await workbook.render({sheetName,autoCrop:'all',scale:1,format:'png'})
await fs.writeFile('.codex-spreadsheet-read/Pemetaan_Sumber_Data.png',new Uint8Array(await preview.arrayBuffer()))
