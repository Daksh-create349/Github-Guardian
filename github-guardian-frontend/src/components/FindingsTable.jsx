import { DataGrid } from '@mui/x-data-grid';

export default function FindingsTable({ columns, rows }) {
  return (
    <div style={{ height: 400, width: '100%', marginTop: '20px' }}>
      <DataGrid rows={rows} columns={columns} pageSize={5} rowsPerPageOptions={[5]} />
    </div>
  );
}
