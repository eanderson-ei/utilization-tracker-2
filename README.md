# README

An app to help EI staff manage towards their utilization target.

Find the app at https://ei-utilization.herokuapp.com.

Data is updated weekly on Monday.

### To maintain

1. Download required files from Deltek

1. Navigate to this [Colab script](https://colab.research.google.com/drive/1Qls4aDysZYLk5XZWPf3ycNkHuKbPvl2e)

1. Upload files in file sidebar

1. Run all cells

1. Update users on Heroku if necessary (see instructions in last two cells)


### To deploy changes

```bash
git pull
git push origin master
git push heroku master
```

