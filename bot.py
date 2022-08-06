#!/usr/bin/env python

import logging
import os
import subprocess
from pathlib import Path
from zipfile import ZipFile

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from configs import Config
from utils import now

INVOICE_TEMPLATE_PATH = Path('invoice_template.odt')

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    bot_token = Config().telegram_bot_token
    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler('start', start))

    application.run_polling()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Creating new invoice...')

    Invoice(INVOICE_TEMPLATE_PATH)


class Invoice:
    PLACEHOLDERS = {
        'INVOICE_NO': now('%m/%y'),
        'INVOICE_DATE': now('%d.%m.%Y')
    }

    TEMP_INVOICE_ODT_PATH = Path(f"data/invoice_{now('%m_%y')}.odt")
    INVOICE_PDF_DIR_PATH = Path(f'data')

    def __init__(self, template_path: Path):
        self._template_path = template_path

        self._create_temp_odt()
        self._convert_odt_to_pdf()
        self._delete_temp_odt()

    def _create_temp_odt(self) -> None:
        with ZipFile(self._template_path) as in_zip, ZipFile(self.TEMP_INVOICE_ODT_PATH, 'w') as out_zip:
            # iterate the input files
            for in_zip_info in in_zip.infolist():
                # read input file
                with in_zip.open(in_zip_info) as in_file:
                    if in_zip_info.filename == 'content.xml':
                        content = in_file.read().decode('utf-8')
                        # replace placeholders with relevant values
                        for placeholder, value in self.PLACEHOLDERS.items():
                            content = content.replace(placeholder, value)

                        out_zip.writestr(in_zip_info.filename, content.encode())
                    else:
                        out_zip.writestr(in_zip_info.filename, in_file.read())

    def _convert_odt_to_pdf(self) -> None:
        """Convert temp ODT to PDF using LibreOffice"""
        command_options = [
            '--headless',
            f'--convert-to',
            f'pdf',
            f'--outdir',
            str(self.INVOICE_PDF_DIR_PATH),
            str(self.TEMP_INVOICE_ODT_PATH)
        ]
        command = subprocess.run(['soffice', *command_options], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if command.returncode != 0:
            error = command.stdout.decode('utf-8')
            raise RuntimeError(f"Failed to convert temp ODT file to PDF: {error}")

    def _delete_temp_odt(self) -> None:
        if os.path.exists(self.TEMP_INVOICE_ODT_PATH):
            os.remove(self.TEMP_INVOICE_ODT_PATH)


if __name__ == '__main__':
    main()
