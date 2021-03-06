from pathlib import Path
import pandas as pd

from dataset_writer import DatasetWriter


class CSVWriter(DatasetWriter):
    def _write_partition(self, dataset_part, output_path: Path, part_id: str = None):
        self._data = pd.DataFrame(columns=['path', 'label'])
        super()._write_partition(dataset_part=dataset_part, output_path=output_path, part_id=part_id)
        self._data.to_csv(output_path, index=False)
        self._data = None

    def _write_example(self, path, label):
        self._data = self._data.append({'path': path, 'label': label}, ignore_index=True, sort=False)

    def _get_extension(self) -> str:
        return "csv"
